from django.contrib.auth import get_user_model
from django.core import validators
from django.db import models


User = get_user_model()
MAX_LENGTH = 200
MAX_LENGTH_COLOR = 7


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MAX_LENGTH,
    )

    class Meta:
        ordering = ('name', )
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='name_unit_unique',
            ),
        )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH,
        unique=True,
    )
    color = models.CharField(
        'Цвет в HEX',
        max_length=MAX_LENGTH_COLOR,
        unique=True,
    )
    slug = models.SlugField(
        'Уникальный слаг',
        max_length=MAX_LENGTH,
        unique=True,
    )

    class Meta:
        ordering = ('name', )
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        'Название рецепта',
        max_length=MAX_LENGTH,
    )
    image = models.ImageField(
        'Ссылка на картинку на сайте',
        upload_to='media/recipes/',
        blank=False,
        null=True,
    )
    text = models.TextField(
        'Описание рецепта',
        help_text='Введите описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Список ингредиентов',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Список тегов',
        related_name='recipes',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[validators.MinValueValidator(
            1, message='Мин. время приготовления 1 минута'), ]
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', )

    def __str__(self):
        return f'{self.name}, {self.author.username}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Название рецепта',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        default=1,
        validators=(
            validators.MinValueValidator(
                1, message='Мин. количество ингридиентов 1'
            ),
        ),
        verbose_name='Количество',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='recipe_ingredient_unique'),
        )


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Название рецепта'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'tag'),
                name='recipe_tag_unique'
            ),
        )


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Название рецепта',
        related_name='shopping_cart',
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='user_recipe_unique'
            ),
        )


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Название рецепта',
        related_name='favorites',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='user_favorite_unique',
            ),
        )
