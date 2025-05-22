from django.urls import path

from recipes.views import recipe_link

app_name = 'recipes'

urlpatterns = [
    path('s/<int:recipe_id>/', recipe_link, name='get_recipe_link'),
]
