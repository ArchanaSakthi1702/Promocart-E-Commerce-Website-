from rest_framework import serializers
from api.models import Product,Feedback

class ProductAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

