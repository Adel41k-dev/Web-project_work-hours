from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

from .models import WorkDay

User = get_user_model()


# ---------------- HOME ----------------
def home(request):
    return render(request, "main/home.html")


# ---------------- REGISTER ----------------
def register(request):
    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        if password1 != password2:
            error = "Passwords do not match"

        elif User.objects.filter(username=username).exists():
            error = "Username exists"

        elif User.objects.filter(email=email).exists():
            error = "Email exists"

        else:
            User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            return redirect("/login/")

    return render(request, "main/register.html", {"error": error})


# ---------------- LOGIN ----------------
def login_view(request):
    error = None

    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password")
        )

        if user:
            login(request, user)

            if user.is_staff:
                return redirect("/admin/")
            return redirect("/profile/")
        else:
            error = "Wrong credentials"

    return render(request, "main/login.html", {"error": error})


# ---------------- PROFILE ----------------
@login_required
def profile(request):
    days = WorkDay.objects.filter(user=request.user).order_by("-start_time")

    date_from = request.GET.get("from")
    date_to = request.GET.get("to")

    if date_from and date_to:
        days = days.filter(start_time__date__range=[date_from, date_to])

    total_hours = sum(d.get_hours() for d in days)
    total_money = sum(d.get_earnings() for d in days)

    active_day = WorkDay.objects.filter(user=request.user, is_active=True).first()

    return render(request, "main/profile.html", {
        "days": days,
        "active_day": active_day,
        "total_hours": total_hours,
        "total_money": total_money
    })


# ---------------- START ----------------
@login_required
def start_day(request):
    if not WorkDay.objects.filter(user=request.user, is_active=True).exists():
        WorkDay.objects.create(user=request.user)
    return redirect("/profile/")


# ---------------- END ----------------
@login_required
def end_day(request):
    active = WorkDay.objects.filter(user=request.user, is_active=True).first()

    if active:
        active.end_time = timezone.now()
        active.is_active = False
        active.save()

    return redirect("/profile/")


# ---------------- ADMIN PANEL ----------------
@login_required
def admin(request):
    if not request.user.is_staff:
        return redirect("/profile/")

    tab = request.GET.get("tab", "dashboard")

    users = User.objects.all()
    workdays = WorkDay.objects.select_related("user").all()

    user_id = request.GET.get("user")
    date = request.GET.get("date")

    if user_id:
        workdays = workdays.filter(user_id=user_id)

    if date:
        workdays = workdays.filter(start_time__date=date)

    total_hours = sum(w.get_hours() for w in workdays)
    total_money = sum(w.get_earnings() for w in workdays)

    return render(request, "main/admin.html", {
        "tab": tab,
        "users": users,
        "workdays": workdays,
        "total_hours": total_hours,
        "total_money": total_money
    })

# ---------------- EDIT USER ----------------
@login_required
def edit_user(request, user_id):
    if not request.user.is_staff:
        return redirect("/profile/")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.username = request.POST.get("username")
        user.email = request.POST.get("email")

        if request.POST.get("password"):
            user.set_password(request.POST.get("password"))

        rate = request.POST.get("hourly_rate")
        if rate:
            user.hourly_rate = float(rate)

        user.save()
        return redirect("/admin/")

    return render(request, "main/edit_user.html", {"user": user})


# ---------------- CHANGE PASSWORD ----------------
@login_required
def change_password(request):
    error = None

    if request.method == "POST":
        if not request.user.check_password(request.POST.get("old")):
            error = "Wrong old password"
        elif request.POST.get("new1") != request.POST.get("new2"):
            error = "Mismatch"
        else:
            request.user.set_password(request.POST.get("new1"))
            request.user.save()
            login(request, request.user)
            return redirect("/profile/")

    return render(request, "main/change_password.html", {"error": error})


# ---------------- LOGOUT ----------------
def logout_view(request):
    logout(request)
    return redirect("/")