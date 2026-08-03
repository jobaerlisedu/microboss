from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'shifts', views.ShiftViewSet)
router.register(r'rosters', views.DutyRosterViewSet)
router.register(r'leave-types', views.LeaveTypeViewSet)
router.register(r'leave-requests', views.LeaveRequestViewSet)
router.register(r'leave-balances', views.LeaveBalanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
