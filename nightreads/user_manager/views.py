from django.views.generic import View
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from nightreads.posts.models import Tag
from .forms import SubscribeForm, UnsubscribeForm, ConfirmEmailForm
from . import user_service


class SubscribeView(View):
    form_class = SubscribeForm

    def get(self, request):
        all_tags = Tag.objects.all()
        return render(request, 'user_manager/index.html', {'tags': all_tags})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            tags = form.cleaned_data['tags']
            user = user_service.get_or_create_user(email=email)
            is_updated = user_service.update_user_tags(user=user, tags=tags)
            if is_updated:
                key = user_service.generate_key(user=user)
                user_service.send_confirmation_email(
                    request=request, user=user, key=key)
                return JsonResponse({'status': 'Email sent'})
            return JsonResponse({'status': 'No tags updated'})
        return JsonResponse({'errors': form.errors})


class UnsubscribeView(View):

    form_class = UnsubscribeForm

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(UnsubscribeView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = user_service.get_user(email=email)
            if not user:
                return JsonResponse({'error': 'User Not Found'})
            key = user_service.generate_key(user=user, for_subscription=False)
            user_service.send_confirmation_email(
                request=request, user=user, key=key, for_subscription=False)
            return JsonResponse({'status': 'Email sent'})
        return JsonResponse({'errors': form.errors})


class ConfirmEmailView(View):

    form_class = ConfirmEmailForm

    def get(self, request):
        form = self.form_class(request.GET)
        if form.is_valid():
            is_subscribed = form.cleaned_data['subscribe']
            user = form.cleaned_data['user']
            user_service.update_subscription(user=user, status=is_subscribed)
            if is_subscribed:
                return JsonResponse({'status': 'Subscribed'})
            else:
                return JsonResponse({'status': 'Unsubscribed'})
        return JsonResponse({'errors': form.errors})
