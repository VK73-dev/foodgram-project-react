from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from djoser.views import UserViewSet

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User, Subscription
from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (CreateRecipeSerializer, FavoriteSerializer,
                             IngredientSerializer, RecipeSerializer,
                             ShoppingCartSerializer, TagSerializer,
                             SubscriptionSerializer)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny, )
    serializer_class = IngredientSerializer
    paginator = None
    filter_backends = (IngredientFilter, )
    search_fields = ('^name', )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    permission_classes = (AllowAny, )
    serializer_class = TagSerializer
    paginator = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly, )
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return CreateRecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @action(detail=True, methods=('post', ),
            permission_classes=(IsAuthenticated, ))
    def shopping_cart(self, request, pk):
        return post_record_model(ShoppingCartSerializer, request, pk, 'recipe')

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        shopping_cart = get_object_or_404(Recipe, id=pk).shopping_cart
        return delete_record_model(shopping_cart, request, pk)

    @action(detail=True, methods=('post', ),
            permission_classes=(IsAuthenticated, ),
            pagination_class=CustomPagination)
    def favorite(self, request, pk):
        return post_record_model(FavoriteSerializer, request, pk, 'recipe')

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        favorites = get_object_or_404(Recipe, id=pk).favorites
        return delete_record_model(favorites, request, pk)

    @action(detail=False)
    def download_shopping_cart(self, request):
        ingredient_list = "Cписок покупок:"
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        for num, ing in enumerate(ingredients):
            ingredient_list += (
                f"\n{ing['ingredient__name']} - "
                f"{ing['amount']} {ing['ingredient__measurement_unit']}"
            )
            if num < ingredients.count() - 1:
                ingredient_list += ', '
        file = 'shopping_list'
        response = HttpResponse(
            ingredient_list, 'Content-Type: application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{file}.pdf"'
        return response


class UserViewSet(UserViewSet):

    def get_permissions(self):
        if self.action == 'retrieve':
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]
        else:
            return super().get_permissions()

    @action(detail=False,
            url_path='subscriptions',
            permission_classes=(IsAuthenticated, ))
    def get_subscriptions(self, request):
        queryset = Subscription.objects.filter(user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=('post', ),
            permission_classes=(IsAuthenticated, ))
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        return post_record_model(
            SubscriptionSerializer, request, author.id, 'author'
        )

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        author = get_object_or_404(User, id=id).author
        return delete_record_model(author, request, id)


def post_record_model(serializer, request, pk, key):
    data = {
        'user': request.user.id,
    }
    data[key] = pk
    serializer = serializer(
        data=data, context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def delete_record_model(model, request, pk):
    record = model.filter(user=request.user)
    if record.exists():
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_400_BAD_REQUEST)
