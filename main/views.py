from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages

from .models import WorkDay

User = get_user_model()


# ---------------- LOGOUT ----------------
def logout_view(request):
    logout(request)
    return redirect("/")


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

        if not username or not email or not password1:
            error = "Fill all fields"

        elif password1 != password2:
            error = "Passwords do not match"

        elif User.objects.filter(username=username).exists():
            error = "Username already exists"

        elif User.objects.filter(email=email).exists():
            error = "Email already exists"

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
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            # 🧠 админ → /admin/
            if user.is_staff:
                return redirect("/admin/")
            else:
                return redirect("/profile/")
        else:
            error = "Wrong credentials"

    return render(request, "main/login.html", {"error": error})


# ---------------- PROFILE ----------------
@login_required
def profile(request):
    days = WorkDay.objects.filter(user=request.user).order_by("-start_time")

    start = request.GET.get("start")
    end = request.GET.get("end")
    min_money = request.GET.get("min_money")

    if start:
        days = days.filter(start_time__date__gte=start)

    if end:
        days = days.filter(start_time__date__lte=end)

    total_hours = sum(d.get_hours() or 0 for d in days)
    total_money = sum(d.get_earnings() or 0 for d in days)

    if min_money:
        days = [d for d in days if d.get_earnings() >= float(min_money)]

    active_day = WorkDay.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    return render(request, "main/profile.html", {
        "days": days,
        "active_day": active_day,
        "total_hours": total_hours,
        "total_money": total_money
    })


# ---------------- START DAY ----------------
@login_required
def start_day(request):
    active_day = WorkDay.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    if not active_day:
        WorkDay.objects.create(user=request.user)

    return redirect("/profile/")


# ---------------- END DAY ----------------
@login_required
def end_day(request):
    active_day = WorkDay.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    if active_day:
        active_day.end_time = timezone.now()
        active_day.is_active = False
        active_day.save()

    return redirect("/profile/")


# ---------------- STATS ----------------
@login_required
def stats(request):
    days = WorkDay.objects.filter(user=request.user)

    total = sum(d.get_hours() or 0 for d in days)

    return render(request, "main/stats.html", {
        "total": round(total, 2)
    })


# ---------------- ADMIN PANEL (/admin/) ----------------
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

    return render(request, "main/admin.html", {
        "tab": tab,
        "users": users,
        "workdays": workdays
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

        password = request.POST.get("password")
        if password:
            user.set_password(password)

        # 💰 зарплата (если добавил поле hourly_rate)
        if hasattr(user, "hourly_rate"):
            rate = request.POST.get("hourly_rate")
            if rate:
                user.hourly_rate = float(rate)

        user.save()

        return redirect("/admin/?tab=users")

    return render(request, "main/edit_user.html", {
        "user": user
    })

@login_required
def change_password(request):
    error = None

    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password1 = request.POST.get("new_password1")
        new_password2 = request.POST.get("new_password2")

        if not request.user.check_password(old_password):
            error = "Wrong old password"

        elif new_password1 != new_password2:
            error = "Passwords do not match"

        elif len(new_password1) < 4:
            error = "Password too short"

        else:
            request.user.set_password(new_password1)
            request.user.save()

            # 🔥 важно — пересоздаём сессию правильно
            user = authenticate(
                username=request.user.username,
                password=new_password1
            )
            login(request, user)

            return redirect("/profile/")

    return render(request, "main/change_password.html", {"error": error})