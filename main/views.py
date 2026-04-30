from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
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
            try:
                validate_email(email)
            except ValidationError:
                error = "Invalid email address"


        if not error:
            try:
                validate_password(password1)
            except ValidationError as e:
                error = " ".join(e.messages)


        if not error:
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

            # 🔥 СУПЕРПОЛЬЗОВАТЕЛЬ → сразу в админку
            if user.is_superuser:
                return redirect("/admin/")

            # обычный пользователь
            return redirect("/profile/")
        else:
            error = "Wrong credentials"

    return render(request, "main/login.html", {"error": error})

# ----------------ADMIN REDICT-------------

from django.shortcuts import redirect

def admin_redirect(request):
    return redirect('/admin-42829/')


# ---------------- PROFILE ----------------
@login_required
def profile(request):
    workdays = WorkDay.objects.filter(user=request.user)

    start_date = request.GET.get("start")
    end_date = request.GET.get("end")
    min_earnings = request.GET.get("min_earnings")
    sort = request.GET.get("sort")

    # ---------------- DATE FILTER ----------------
    if start_date:
        workdays = workdays.filter(start_time__date__gte=start_date)

    if end_date:
        workdays = workdays.filter(start_time__date__lte=end_date)

    # ---------------- MIN EARNINGS ----------------
    if min_earnings:
        try:
            min_earnings = float(min_earnings)
            workdays = [w for w in workdays if w.get_earnings() >= min_earnings]
        except:
            pass

    # ---------------- SORT ----------------
    if sort == "hours":
        workdays = sorted(workdays, key=lambda x: x.get_hours(), reverse=True)

    elif sort == "earnings":
        workdays = sorted(workdays, key=lambda x: x.get_earnings(), reverse=True)

    elif sort == "date":
        workdays = sorted(workdays, key=lambda x: x.start_time, reverse=True)

    # ---------------- STATS (ВАЖНО: workdays, не days) ----------------
    total_hours = sum(d.get_hours() for d in workdays)
    total_money = sum(d.get_earnings() for d in workdays)

    active_day = WorkDay.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    return render(request, "main/profile.html", {
        "days": workdays,
        "total_hours": total_hours,
        "total_money": total_money,
        "active_day": active_day,
    })


# ---------------- START DAY ----------------
@login_required
def start_day(request):
    active = WorkDay.objects.filter(user=request.user, is_active=True).exists()

    if not active:
        WorkDay.objects.create(
            user=request.user,
            start_time=timezone.now(),
            is_active=True
        )

    return redirect("/profile/")


# ---------------- END DAY ----------------
@login_required
def end_day(request):
    active = WorkDay.objects.filter(user=request.user, is_active=True).first()

    if active:
        active.end_time = timezone.now()
        active.is_active = False
        active.save()

    return redirect("/profile/")


# ---------------- ADMIN PANEL (🔥 UPGRADED) ----------------
@login_required
def admin(request):
    if not request.user.is_superuser:
        return redirect("/profile/")

    tab = request.GET.get("tab", "users")

    users = User.objects.exclude(is_superuser=True)
    workdays = WorkDay.objects.select_related("user").all()

    # ---------------- FILTERS ----------------
    user_id = request.GET.get("user")
    start_date = request.GET.get("start")
    end_date = request.GET.get("end")
    min_earnings = request.GET.get("min_earnings")
    sort = request.GET.get("sort")

    if user_id:
        workdays = workdays.filter(user_id=user_id)

    if start_date:
        workdays = workdays.filter(start_time__date__gte=start_date)

    if end_date:
        workdays = workdays.filter(start_time__date__lte=end_date)

    # ---------------- MIN EARNINGS (computed field) ----------------
    if min_earnings:
        min_earnings = float(min_earnings)
        workdays = [w for w in workdays if w.get_earnings() >= min_earnings]

    # ---------------- SORTING ----------------
    if sort == "hours":
        workdays = sorted(workdays, key=lambda x: x.get_hours(), reverse=True)

    elif sort == "earnings":
        workdays = sorted(workdays, key=lambda x: x.get_earnings(), reverse=True)

    elif sort == "date":
        workdays = sorted(workdays, key=lambda x: x.start_time, reverse=True)

    # ---------------- TOTAL STATS ----------------
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
    error = None

    if request.method == "POST":
        new_username = request.POST.get("username")
        new_email = request.POST.get("email")
        password = request.POST.get("password")

        # ---------------- USERNAME ----------------
        if new_username != user.username:
            if User.objects.exclude(id=user.id).filter(username=new_username).exists():
                error = "Username already exists"
            else:
                user.username = new_username

        # ---------------- EMAIL ----------------
        if not error and new_email != user.email:
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError

            try:
                validate_email(new_email)
            except ValidationError:
                error = "Invalid email address"

            if not error and User.objects.exclude(id=user.id).filter(email=new_email).exists():
                error = "Email already exists"

            if not error:
                user.email = new_email

        # ---------------- PASSWORD ----------------
        if not error and password:
            try:
                from django.contrib.auth.password_validation import validate_password
                validate_password(password, user)
                user.set_password(password)
            except ValidationError as e:
                error = " ".join(e.messages)

        # ---------------- SAVE ----------------
        if not error:
            rate = request.POST.get("hourly_rate")
            if rate:
                user.hourly_rate = float(rate)

            user.save()
            return redirect("/admin/")

    return render(request, "main/edit_user.html", {
        "user": user,
        "error": error
    })


# ---------------- CHANGE PASSWORD ----------------
@login_required
def change_password(request):
    error = None

    if request.method == "POST":
        old = request.POST.get("old")
        new1 = request.POST.get("new1")
        new2 = request.POST.get("new2")

        if not request.user.check_password(old):
            error = "Wrong old password"

        elif new1 != new2:
            error = "Passwords do not match"

        else:
            try:
                validate_password(new1, request.user)  # 🔐 проверка
            except ValidationError as e:
                error = " ".join(e.messages)

            if not error:
                request.user.set_password(new1)
                request.user.save()
                login(request, request.user)
                return redirect("/profile/")

    return render(request, "main/change_password.html", {"error": error})


# ---------------- LOGOUT ----------------
def logout_view(request):
    logout(request)
    return redirect("/")

@login_required
def account_view(request):
    user = request.user

    return render(request, "main/account.html", {
        "user": user
    })

@login_required
def edit_name(request):
    if request.method == "POST":
        request.user.username = request.POST.get("username")
        request.user.save()
        return redirect("account")

    return render(request, "main/change_name.html")

@login_required
def edit_email(request):
    error = None

    if request.method == "POST":
        new_email = request.POST.get("email", "").strip()

        # 1. формат email
        try:
            validate_email(new_email)
        except ValidationError:
            error = "Invalid email address"

        # 2. такой же как старый
        if not error and new_email == request.user.email:
            error = "This is already your current email"

        # 3. уже занят другим пользователем
        if not error and User.objects.exclude(id=request.user.id).filter(email=new_email).exists():
            error = "Email already exists"

        # 4. сохранить
        if not error:
            request.user.email = new_email
            request.user.save()
            return redirect("account")

    return render(request, "main/change_email.html", {
        "error": error
    })


@login_required
def clear_history(request, work_id):
    if request.method == "POST":
        workday = get_object_or_404(WorkDay, id=work_id, user=request.user)
        workday.delete()

    return redirect('profile')

@login_required
def admin_delete_workday(request, work_id):
    if not request.user.is_staff:
        return redirect("/profile/")

    workday = get_object_or_404(WorkDay, id=work_id)
    workday.delete()

    return redirect("/admin/?tab=worklogs")