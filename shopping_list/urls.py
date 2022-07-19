from django.urls import path, include

from shopping_list.api.views import ListAddShoppingList, ShoppingListDetail, AddShoppingItem, ShoppingItemDetail

urlpatterns = [
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api/shopping-lists/", ListAddShoppingList.as_view(), name="all_shopping_lists"),
    path("api/shopping-lists/<uuid:pk>/", ShoppingListDetail.as_view(), name="shopping_list_detail"),
    path("api/shopping-lists/<uuid:pk>/shopping-items/", AddShoppingItem.as_view(), name="add_shopping_item"),
    path("api/shopping-lists/<uuid:pk>/shopping-items/<uuid:item_pk>/", ShoppingItemDetail.as_view(), name="shopping_item_detail"),
]