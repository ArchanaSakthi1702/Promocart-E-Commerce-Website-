from rest_framework import serializers
from .models import CustomUser,Product,Order,OrderItem,OrderStatus,Category,SubCategory,Brand,Feedback,CartItem
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'phone', 'address', 'password']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data.get('name'),
            phone=validated_data.get('phone'),
            address=validated_data.get('address'),
        )
        return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom fields to the token if needed
        token['email'] = user.email
        token['name'] = user.name
        return token

    def validate(self, attrs):
        # replace 'username' with 'email'
        attrs['username'] = attrs.get('email')
        return super().validate(attrs)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'phone', 'address', 'password', 'profile_picture']

    def create(self, validated_data):
        profile_picture = validated_data.pop('profile_picture', None)

        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data.get('name'),
            phone=validated_data.get('phone'),
            address=validated_data.get('address'),
        )

        if profile_picture:
            user.profile_picture = profile_picture
            user.save()

        return user


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product not found.")
        return value
    

   
class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(use_url=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'phone', 'address', 'profile_picture']
        read_only_fields = ['email']



class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status = serializers.PrimaryKeyRelatedField(queryset=OrderStatus.objects.all())

    class Meta:
        model = Order
        fields = ['id', 'user', 'created_at', 'total_price', 'status', 'items']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['status_name'] = instance.status.name  # Add readable name
        return data
    


class ProductListSerializer(serializers.ModelSerializer):
    brand = serializers.CharField(source='brand.name')  # Show brand name

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image', 'brand']



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name'] 


class SubCategorySerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()  # or use CategorySerializer if needed

    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'category']

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']



class CreateFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['product', 'message']


class FeedbackSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    product = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Feedback
        fields = ['id', 'user', 'user_id', 'product', 'message', 'created_at', 'is_resolved']




class ProductDetailSerializer(serializers.ModelSerializer):
    brand = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    subcategory = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'price',
            'description',
            'image',
            'brand',
            'category',
            'subcategory',
            'stock',
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['product_name', 'quantity', 'price']

class OrderTrackSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True) 
    status = serializers.CharField(source='status.name', read_only=True)  # <-- this uses 'items' not 'orderitem_set'

    class Meta:
        model = Order
        fields = ['id', 'created_at', 'total_price', 'status', 'items']

class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'product_name', 'product_price', 'product_image', 'quantity', 'subtotal']

    def get_subtotal(self, obj):
        return obj.quantity * obj.product.price
