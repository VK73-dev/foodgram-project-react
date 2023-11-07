from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Ingredient, Tag, Recipe, RecipeIngredient,
                            RecipeTag, ShoppingCart, Favorite)
from users.models import User, Subscription


class CustomUserCreateSerializer(UserCreateSerializer):

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


class CustomUserSerializer(UserSerializer):
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
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


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
    author = CustomUserSerializer(read_only=True)
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
        return Favorite.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()


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


class CreateRecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
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
        for ing in ingredients:
            ingredient = Ingredient.objects.get(id=ing['id'])
            RecipeIngredient.objects.create(
                ingredient=ingredient,
                recipe=recipe,
                amount=ing['amount'],
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
        RecipeTag.objects.filter(recipe=instance).delete()
        RecipeIngredient.objects.filter(recipe=instance).delete()
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


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return ShowFavoriteSerializer(instance.recipe, context={
            'request': self.context.get('request')
        }).data


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return ShowFavoriteSerializer(instance.recipe, context={
            'request': self.context.get('request')
        }).data


class ShowSubscriptionsSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
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

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        recipes = Recipe.objects.filter(author=obj)
        limit = request.query_params.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        return ShowFavoriteSerializer(
            recipes, many=True, context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


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
            if Subscription.objects.filter(
                    user=data['user'],
                    author=data['author']
            ).exists():
                raise serializers.ValidationError(
                    'Вы уже подписаны на этого автора'
                )
            return data

    def to_representation(self, instance):
        return ShowSubscriptionsSerializer(instance.author, context={
            'request': self.context.get('request')
        }).data
