from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('me/', views.CurrentUserView.as_view(), name='current-user'),
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<hexuuid:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<uuid:user_id>/reset-password/', views.AdminResetPasswordView.as_view(), name='admin-reset-pw'),
    path('users/<uuid:user_id>/toggle-admin/', views.ToggleAdminView.as_view(), name='toggle-admin'),
    path('sessions/', views.UserSessionsView.as_view(), name='user-sessions'),
    path('sessions/all/', views.AllSessionsView.as_view(), name='all-sessions'),
    path('sessions/<uuid:session_id>/logout/', views.RemoteLogoutView.as_view(), name='remote-logout'),
    path('password-reset/request/', views.PasswordResetRequestView.as_view(), name='pw-reset-request'),
    path('password-reset/verify/', views.PasswordResetVerifyView.as_view(), name='pw-reset-verify'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='pw-reset-confirm'),
]
