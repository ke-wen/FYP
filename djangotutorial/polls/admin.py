from django.contrib import admin
from import_export import resources
from .models import Choice, Question, House
from import_export.admin import ImportExportModelAdmin


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("Date information", {"fields": ["pub_date"], "classes": ["collapse"]}),
    ]
    inlines = [ChoiceInline]
    list_display = ["question_text", "pub_date", "was_published_recently"]
    list_filter = ["pub_date"]
    search_fields = ["question_text"]

class HouseResource(resources.ModelResource):
    class Meta:
        model = House

class HouseAdmin(ImportExportModelAdmin):
    resource_class = HouseResource
    list_display = ('address', 'county', 'price', 'date_of_sale', 'description_of_property')
    list_filter = ('county', 'date_of_sale')
    search_fields = ('address', 'description_of_property')

admin.site.register(House, HouseAdmin)
admin.site.register(Question, QuestionAdmin)
