from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (MyTokenObtainPairSerializer,RegisterSerializer,
                          AddToCartSerializer,UserProfileSerializer,OrderSerializer,
                          ProductListSerializer,CategorySerializer,BrandSerializer,SubCategorySerializer,
                          CreateFeedbackSerializer,FeedbackSerializer,ProductDetailSerializer,
                          OrderTrackSerializer,CartItemSerializer)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status,viewsets
from .models import Product,Cart,CartItem, Order, OrderItem,StoreSetting,OrderStatus,Category,Brand,SubCategory,Feedback
from django.db import transaction
from rest_framework.permissions import IsAuthenticated,AllowAny
from .pagination import ProductPagination,UserOrdersPagination
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class RegisterView(APIView):
    def post(self, request):
        # Normalize data: if any field is a list, extract the first item
        normalized_data = {
            key: (value[0] if isinstance(value, list) else value)
            for key, value in request.data.items()
        }

        serializer = RegisterSerializer(data=normalized_data)
        print("Normalized:", normalized_data)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductPublicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductDetailSerializer
    permission_classes = []  # Allow any



class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data['quantity']
            print(product_id,quantity)

            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

            # Get or create cart for user
            cart, _ = Cart.objects.get_or_create(user=request.user)

            # Get or create cart item
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

            new_quantity = quantity if created else cart_item.quantity + quantity

            # Check against stock
            if new_quantity > product.stock:
                return Response(
                    {"error": f"Only {product.stock} units in stock. You already have {cart_item.quantity} in cart."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update quantity and save
            cart_item.quantity = new_quantity
            cart_item.save()

            return Response({"message": "Product added to cart."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RemoveFromCartView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, cart_item_id):
        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
            cart_item.delete()
            return Response({"message": "Item removed from cart."}, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found in cart."}, status=status.HTTP_404_NOT_FOUND)




class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        print(request.data)
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            s2=serializer = UserProfileSerializer(request.user, context={'request': request})
            return Response({"message": "Profile updated successfully.", "user": s2.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile fully updated.", "user": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    

class UserDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.delete()
        return Response({"detail": "User profile deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def place_order_view(request):
    user = request.user
    try:
        cart = user.cart
        cart_items = cart.items.all()

        if not cart_items.exists():
            return Response({"error": "Cart is empty."}, status=400)

        total = sum([item.quantity * item.product.price for item in cart_items])

        with transaction.atomic():
            # ✅ Get the default order status (e.g., ID=3)
            default_status = OrderStatus.objects.get(name="Order Received")

            order = Order.objects.create(
                user=user,
                total_price=total,
                status=default_status
            )

            # ✅ Get StoreSetting once before the loop
            store_setting = StoreSetting.objects.first()

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

                if store_setting and store_setting.auto_stock_deduction:
                    item.product.stock -= item.quantity
                    item.product.save()

            # Clear cart
            cart.items.all().delete()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=201)

    except Cart.DoesNotExist:
        return Response({"error": "Cart not found."}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_now_view(request):
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))
    print(product_id,quantity)

    if not product_id:
        return Response({"error": "Product ID is required."}, status=400)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": "Product not found."}, status=404)

    if product.stock < quantity:
        return Response({"error": "Not enough stock available."}, status=400)

    total_price = product.price * quantity

    with transaction.atomic():
        # ✅ Get the default order status (e.g., with ID = 3)
        default_status = OrderStatus.objects.get(name="Order Received")

        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            status=default_status  # Correct: assign instance, not string
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price
        )

        setting = StoreSetting.objects.first()
        if setting and setting.auto_stock_deduction:
            product.stock -= quantity
            product.save()

    return Response({
        "message": "Order placed successfully.",
        "order_id": order.id,
        "product": product.name,
        "quantity": quantity,
        "total_price": total_price
    }, status=201)


@api_view(['GET'])
def list_products_view(request):
    products = Product.objects.all()
    paginator = ProductPagination()
    result_page = paginator.paginate_queryset(products, request)
    serializer = ProductListSerializer(result_page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)




@api_view(['GET'])
def list_categories_view(request):
    categories = Category.objects.all()

    paginator = PageNumberPagination()
    paginator.page_size = 10  # or set default in settings.py
    result_page = paginator.paginate_queryset(categories, request)

    serializer = CategorySerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)




@api_view(['GET'])
def list_subcategories_view(request):
    subcategories = SubCategory.objects.all()
    paginator = PageNumberPagination()
    paginator.page_size = 10
    result_page = paginator.paginate_queryset(subcategories, request)
    serializer = SubCategorySerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def list_brands_view(request):
    brands = Brand.objects.all()
    paginator = PageNumberPagination()
    paginator.page_size = 10
    result_page = paginator.paginate_queryset(brands, request)
    serializer = BrandSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_feedback_view(request):
    serializer = CreateFeedbackSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response({"message": "Feedback submitted successfully."}, status=201)
    return Response(serializer.errors, status=400)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def edit_feedback_view(request, feedback_id):
    try:
        feedback = Feedback.objects.get(id=feedback_id, user=request.user)
    except Feedback.DoesNotExist:
        return Response({"error": "Feedback not found or unauthorized."}, status=404)

    serializer = CreateFeedbackSerializer(feedback, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Feedback updated successfully."})
    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_feedback_view(request):
    feedbacks = Feedback.objects.filter(user=request.user).order_by('-created_at')
    serializer = FeedbackSerializer(feedbacks, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])  # Or IsAuthenticated if needed
def list_feedbacks_for_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    feedbacks = Feedback.objects.filter(product=product).select_related('user').order_by('-created_at')
    serializer = FeedbackSerializer(feedbacks, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_feedback_view(request, feedback_id):
    try:
        feedback = Feedback.objects.get(id=feedback_id, user=request.user)
    except Feedback.DoesNotExist:
        return Response({"error": "Feedback not found or unauthorized."}, status=404)

    feedback.delete()
    return Response({"message": "Feedback deleted successfully."}, status=204)

@api_view(['GET'])
def product_detail_view(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProductDetailSerializer(product, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_orders_view(request):
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at')

    paginator = UserOrdersPagination()  # instantiate it
    paginated_orders = paginator.paginate_queryset(orders, request)  # pass both arguments

    serializer = OrderTrackSerializer(paginated_orders, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_cart_view(request):
    user = request.user
    try:
        cart = user.cart  # Assuming OneToOneField from User to Cart
    except Cart.DoesNotExist:
        return Response({"error": "Cart not found."}, status=404)

    items = cart.items.all()  # Assuming related_name='items' in CartItem FK to Cart
    serializer = CartItemSerializer(items, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_item_count_view(request):
    user = request.user
    try:
        cart = user.cart  # Assuming OneToOneField from User to Cart
    except Cart.DoesNotExist:
        return Response({"count": 0})  # Return 0 if cart does not exist

    count = cart.items.count()  # Assuming related_name='items' in CartItem
    return Response({"count": count})


@api_view(['GET'])
def search_products_view(request):
    query = request.GET.get('q', '').strip().lower()  # generic 'q' parameter

    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(brand__name__icontains=query) |
            Q(category__name__icontains=query) |
            Q(subcategory__name__icontains=query)
        )

    paginator = ProductPagination()
    result_page = paginator.paginate_queryset(products, request)
    serializer = ProductListSerializer(result_page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def products_by_category_view(request, category_id):
    products = Product.objects.filter(category_id=category_id)
    paginator = ProductPagination()
    result_page = paginator.paginate_queryset(products, request)
    serializer = ProductListSerializer(result_page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def products_by_brand_view(request, brand_id):
    products = Product.objects.filter(brand_id=brand_id)
    paginator = ProductPagination()
    result_page = paginator.paginate_queryset(products, request)
    serializer = ProductListSerializer(result_page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
def products_by_subcategory_view(request, subcategory_id):
    products = Product.objects.filter(subcategory_id=subcategory_id)
    paginator = ProductPagination()
    result_page = paginator.paginate_queryset(products, request)
    serializer = ProductListSerializer(result_page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
    except TokenError:
        return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
def products_by_category_ids_view(request):
    ids = request.GET.get('ids', '')
    id_list = [int(pk) for pk in ids.split(',') if pk.isdigit()]
    products = Product.objects.filter(category_id__in=id_list)

    paginator = ProductPagination()
    result_page = paginator.paginate_queryset(products, request)
    serializer = ProductListSerializer(result_page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def products_by_brand_ids_view(request):
    ids = request.GET.get('ids', '')
    id_list = [int(pk) for pk in ids.split(',') if pk.isdigit()]
    products = Product.objects.filter(brand_id__in=id_list)

    paginator = ProductPagination()
    result_page = paginator.paginate_queryset(products, request)
    serializer = ProductListSerializer(result_page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
def products_by_subcategory_ids_view(request):
    ids = request.GET.get('ids', '')
    id_list = [int(pk) for pk in ids.split(',') if pk.isdigit()]
    products = Product.objects.filter(subcategory_id__in=id_list)

    paginator = ProductPagination()
    result_page = paginator.paginate_queryset(products, request)
    serializer = ProductListSerializer(result_page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)
