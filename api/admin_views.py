from rest_framework import viewsets, permissions,generics
from api.models import Product
from api.admin_serializers import ProductAdminSerializer

class ProductAdminViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductAdminSerializer
    permission_classes = [permissions.IsAdminUser]


class ProductUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductAdminSerializer
    permission_classes = [permissions.IsAdminUser]  # ✅ Only admin can access

    lookup_field = 'pk'  # or 'id' if you prefer

class ProductDeleteView(generics.DestroyAPIView):
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'pk'  # or 'id' as per your model