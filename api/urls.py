from django.urls import path
from .views import MyTokenObtainPairView,RegisterView
from rest_framework_simplejwt.views import TokenRefreshView
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.admin_views import ProductAdminViewSet,ProductUpdateView,ProductDeleteView
from api.views import (AddToCartView,RemoveFromCartView,
                       UpdateProfileView,UserProfileView,UserDeleteView,
                       place_order_view,buy_now_view,list_products_view,
                       list_categories_view,list_subcategories_view,list_brands_view,
                       create_feedback_view,list_user_feedback_view,product_detail_view,
                       user_orders_view,my_cart_view,edit_feedback_view,
                       delete_feedback_view,search_products_view,
                       products_by_category_view,products_by_brand_view,
                       products_by_subcategory_view,logout_view,cart_item_count_view,
                       list_feedbacks_for_product,products_by_brand_ids_view,
                       products_by_category_ids_view,products_by_subcategory_ids_view)

router = DefaultRouter()
router.register(r'admin/products', ProductAdminViewSet, basename='admin-products')


urlpatterns = [
    path('', include(router.urls)),
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),

    path('admin/products/<int:pk>/update/', ProductUpdateView.as_view(), name='product-update'),
    path('admin/products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),

    path('cart/add/', AddToCartView.as_view(), name='add-to-cart'),
    path('cart/remove/<int:cart_item_id>/', RemoveFromCartView.as_view(), name='remove-from-cart'),
    path('cart/count/', cart_item_count_view, name='cart-item-count'),

    path('search-products/', search_products_view, name='search-products'),
    path('products/category/<int:category_id>/', products_by_category_view),
    path('products/brand/<int:brand_id>/', products_by_brand_view),
    path('products/subcategory/<int:subcategory_id>/', products_by_subcategory_view),

    path('products/by-category-ids/', products_by_category_ids_view),
    path('products/by-brand-ids/', products_by_brand_ids_view),
    path('products/by-subcategory-ids/', products_by_subcategory_ids_view),

    path('user/profile/update/', UpdateProfileView.as_view(), name='update-profile'),
    path('user/profile/', UserProfileView.as_view(), name='user-profile'),
    path('user/delete/', UserDeleteView.as_view(), name='user-delete'),
    path('logout/', logout_view, name='logout'),

    path('products/<int:pk>/', product_detail_view, name='product-detail'),
    path('my-cart/', my_cart_view, name='my-cart'),
    path('place-order/', place_order_view, name='place-order'),
    path('buy-now/', buy_now_view, name='buy-now'),
    path('my-orders/', user_orders_view, name='user-orders'),

    path('products/', list_products_view, name='product-list'),
    path('categories/', list_categories_view, name='list-categories'),
    path('subcategories/', list_subcategories_view, name='list-subcategories'),
    path('brands/', list_brands_view, name='list-brands'),

    path('feedback/create/', create_feedback_view, name='create-feedback'),
    path('feedback/<int:feedback_id>/edit/', edit_feedback_view, name='edit-feedback'),
    path('feedback/my/', list_user_feedback_view, name='list-user-feedback'),
    path('feedback/<int:feedback_id>/delete/', delete_feedback_view, name='delete-feedback'),
    path('feedback/product/<int:product_id>/', list_feedbacks_for_product, name='list-product-feedbacks'),

]
