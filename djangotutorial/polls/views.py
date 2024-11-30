from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.http import Http404
from django.utils import timezone
from .models import House
from .models import AverageRent, AverageHousePrice


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_housesprice_list"

    def get_queryset(self):
        return AverageHousePrice.objects.all()[:5]

def list_houses(request):
    houses = House.objects.all()  # get list of all house
    return render(request, 'polls/list_houses.html', {'houses': houses})


def show_data(request):

    average_rent_data = AverageRent.objects.filter(eircode='Dublin 1').first()
    average_house_price_data = AverageHousePrice.objects.filter(eircode='D01: Dublin 1').first()

    context = {
        'average_rent_data': average_rent_data,
        'average_house_price_data': average_house_price_data,
    }
    return render(request, 'polls/show_data.html', context)





