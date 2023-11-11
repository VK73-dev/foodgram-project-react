from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient,
                            Recipe, RecipeIngredient,
                            RecipeTag, ShoppingCart, Tag)
from users.models import User, Subscription


class UserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class UserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return obj.author.filter(user=request.user.id).exists()


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return obj.favorites.filter(user=request.user.id).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return obj.shopping_cart.filter(user=request.user.id).exists()


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'amount',
            'measurement_unit',
        )


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError('Мин. количество ингридиентов 1')
        return value


class CreateRecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = AddIngredientRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients or ingredients == []:
            raise serializers.ValidationError({
                'ingredient': ('Поле ингредиент не должно отсутствовать'
                               ' или быть пустым!')
            })
        list_ingredients = []
        for ingredient in ingredients:
            if not Ingredient.objects.filter(id=ingredient['id']).exists():
                raise serializers.ValidationError({
                    'ingredient': 'Такого ингредиента не существует!'
                })
            amount = ingredient['amount']
            if int(amount) < 1:
                raise serializers.ValidationError({
                    'amount': 'Количество ингредиента не должно быть меньше 0!'
                })
            if ingredient['id'] in list_ingredients:
                raise serializers.ValidationError({
                    'ingredient': 'Ингредиенты не должны повторяться!'
                })
            list_ingredients.append(ingredient['id'])

        image = self.initial_data.get('image')
        if image == '':
            raise serializers.ValidationError({
                'image': 'Поле не должно быть пустым!'
            })

        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Поле tags отсутствует!'
            })
        if tags == []:
            raise serializers.ValidationError({
                'tags': 'Поле не должно быть пустым!'
            })
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError({
                'tags': 'Теги повторяются!'
            })
        return data

    def create_ingredients(self, ingredients, recipe):
        list_ingredients = []
        for ing in ingredients:
            ingredient = Ingredient.objects.get(id=ing['id'])
            list_ingredients.append(RecipeIngredient(
                ingredient=ingredient,
                recipe=recipe,
                amount=ing['amount'],
            ))
        RecipeIngredient.objects.bulk_create(
            list_ingredients
        )

    def create_tags(self, tags, recipe):
        for tag in tags:
            RecipeTag.objects.create(recipe=recipe, tag=tag)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.create_ingredients(ingredients, recipe)
        self.create_tags(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        instance.recipe_tags.clear()
        instance.recipe_ingredients.clear()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        self.create_ingredients(ingredients, instance)
        self.create_tags(tags, instance)
        instance.name = validated_data.pop('name')
        instance.text = validated_data.pop('text')
        if validated_data.get('image'):
            instance.image = validated_data.pop('image')
        instance.cooking_time = validated_data.pop('cooking_time')
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class ShowFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class ShoppingCartandFavorite(serializers.ModelSerializer):

    class Meta:
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return ShowFavoriteSerializer(instance.recipe, context={
            'request': self.context.get('request')
        }).data


class ShoppingCartSerializer(ShoppingCartandFavorite):

    class Meta(ShoppingCartandFavorite.Meta):
        model = ShoppingCart

    def validate_recipe(self, value):
        request = self.context.get('request')
        if value.shopping_cart.filter(user=request.user.id).exists():
            raise serializers.ValidationError('Рецепт уже в корзине')
        return value


class FavoriteSerializer(ShoppingCartandFavorite):

    class Meta(ShoppingCartandFavorite.Meta):
        model = Favorite

    def validate_recipe(self, value):
        request = self.context.get('request')
        if value.favorites.filter(user=request.user.id).exists():
            raise serializers.ValidationError('Рецепт уже в избранном')
        return value


class ShowSubscriptionsSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        return ShowFavoriteSerializer(
            recipes, many=True, context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = (
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
            ),
        )

    def validate(self, data):
        if self.context['request'].method == 'POST':
            if data['user'] == data['author']:
                raise serializers.ValidationError(
                    'Нельзя подписаться на самого себя'
                )
            return data

    def to_representation(self, instance):
        return ShowSubscriptionsSerializer(instance.author, context={
            'request': self.context.get('request')
        }).data
