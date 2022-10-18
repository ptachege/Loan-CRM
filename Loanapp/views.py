# from weasyprint import HTML
from django.views.generic import View
from collections import Counter
import calendar
from django.db.models import Sum
from cmath import exp
from time import time
from django.utils.dateparse import parse_date
from datetime import date, datetime, timedelta
import math
from django.utils import timezone
from django.db.models import Q
import json
from django.core.exceptions import ObjectDoesNotExist
import random
from django.contrib.auth import authenticate, login, logout
from email import message
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required


# from django.core.files.storage import FileSystemStorage
# from django.template.loader import render_to_string
from .models import *
from .forms import *
# from .process import html_to_pdf

# Create your views here.


def compute_penalties(request):
    all_active_loans = Loans.objects.filter(
        status="DISBURSED"
    )
    now_date = getcurrenttime()
    if len(all_active_loans) > 0:
        for each_loan in all_active_loans:
            if each_loan.run_penalty_date < now_date:
                # add loan
                extended_days = now_date - each_loan.endpayment_at
                extended_days = extended_days.days

                if extended_days <= 8:
                    current_penalty = each_loan.penalty

                    penalty = 0.06 * each_loan.expected_amount
                    print(current_penalty)
                    each_loan.penalty = penalty
                    each_loan.run_penalty_date = each_loan.endpayment_at + \
                        timedelta(days=7)
                    each_loan.amount_remain = (
                        each_loan.amount_remain - current_penalty) + penalty
                    each_loan.save()

                    # this_loan last installment
                    last_inst = Installments.objects.filter(
                        loan=each_loan
                    ).last()

                    last_inst.expected_amount += penalty
                    last_inst.remaining_amount += penalty
                    last_inst.save()

                elif extended_days > 8 and extended_days <= 19:
                    current_penalty = each_loan.penalty
                    penalty = 0.10 * each_loan.expected_amount
                    each_loan.penalty = penalty
                    each_loan.run_penalty_date = each_loan.endpayment_at + \
                        timedelta(days=19)
                    each_loan.amount_remain = (
                        each_loan.amount_remain - current_penalty) + penalty
                    each_loan.save()

                    # this_loan last installment
                    last_inst = Installments.objects.filter(
                        loan=each_loan
                    ).last()
                    last_inst.expected_amount = (
                        last_inst.expected_amount - current_penalty) + penalty
                    last_inst.remaining_amount = (
                        last_inst.remaining_amount - current_penalty) + penalty
                    last_inst.save()

                elif extended_days > 19:
                    current_penalty = each_loan.penalty
                    penalty = 0.12 * each_loan.expected_amount
                    each_loan.penalty = penalty
                    each_loan.run_penalty_date = each_loan.endpayment_at + \
                        timedelta(days=60)

                    each_loan.amount_remain = (
                        each_loan.amount_remain - current_penalty) + penalty
                    each_loan.save()

                    last_inst = Installments.objects.filter(
                        loan=each_loan
                    ).last()
                    last_inst.expected_amount = (
                        last_inst.expected_amount - current_penalty) + penalty
                    last_inst.remaining_amount = (
                        last_inst.remaining_amount - current_penalty) + penalty
                    last_inst.save()

                return HttpResponse('great')
            else:
                return HttpResponse('too bad')
    else:
        return HttpResponse('Very bad')


@login_required
def index(request):

    if request.user.userprofiles.role == 'Admin':
        current_branch = request.session['current_branch']
        if current_branch == 'all':
            branch_name = 'All'

            new_loans_today = Loans.objects.filter(
                applied_at=getcurrenttime()).count()

            denied_loans_today = Loans.objects.filter(
                denied_at=getcurrenttime()).count()

            approved_loans_today = Loans.objects.filter(
                approved_at=getcurrenttime()).count()

            disbursed_loans_today = Loans.objects.filter(
                disbursed_at=getcurrenttime()).count()

            label2 = ['NEW', 'DENIED', 'APPROVED', 'DISBURSED']
            data2 = [new_loans_today, denied_loans_today,
                     approved_loans_today, disbursed_loans_today]

            # week
            one_week_before = getcurrenttime() - timedelta(days=7)
            new_loans_this_week = Loans.objects.filter(
                applied_at__range=[one_week_before, getcurrenttime()]).count()

            denied_loans_this_week = Loans.objects.filter(
                denied_at__range=[one_week_before, getcurrenttime()]).count()

            approved_loans_this_week = Loans.objects.filter(
                approved_at__range=[one_week_before, getcurrenttime()]).count()

            disbursed_loans_this_week = Loans.objects.filter(
                disbursed_at__range=[one_week_before, getcurrenttime()]).count()

            label4 = ['NEW', 'DENIED', 'APPROVED', 'DISBURSED']
            data4 = [new_loans_this_week, denied_loans_this_week,
                     approved_loans_this_week, disbursed_loans_this_week]

            # month
            current_month = getcurrenttime().month
            new_loans_this_month = Loans.objects.filter(
                applied_at__month=current_month).count()

            denied_loans_this_month = Loans.objects.filter(
                denied_at__month=current_month).count()

            approved_loans_this_month = Loans.objects.filter(
                approved_at__month=current_month).count()

            disbursed_loans_this_month = Loans.objects.filter(
                disbursed_at__month=current_month).count()

            label5 = ['NEW', 'DENIED', 'APPROVED', 'DISBURSED']
            data5 = [new_loans_this_month, denied_loans_this_month,
                     approved_loans_this_month, disbursed_loans_this_month]

            # SECOND ANALYSIS OF NUMBER OF LOANS

            county_model = Loans.objects.all().values_list("applied_at")

            county_count_rep = Counter([rep[0] for rep in county_model])
            county_amount_rep = {}

            for rep in county_count_rep:
                county_amount_rep[rep] = 0

            for month in county_model:
                for rep in county_amount_rep:
                    if month[0] == rep:
                        county_amount_rep[rep] += 1

            label3 = list(county_amount_rep.keys())
            data3 = list(county_amount_rep.values())

            new_loans = Borrowers.objects.filter(
                registerd_on=getcurrenttime()).count()
            borrowers = Borrowers.objects.all().count()
            active_loans = Loans.objects.filter(status="DISBURSED").count()
            officers = UserProfiles.objects.all().count()
            loans_pending_approval = Loans.objects.filter(status="NEW").count()
            loans_pending_disburse = Loans.objects.filter(
                status="APPROVED").count()

            loans_due_today_query = Installments.objects.filter(
                expected_date=getcurrenttime())
            payments_today_query = Transactions.objects.filter(
                date_of_payment=getcurrenttime())

            if len(payments_today_query) >= 1:
                payments_today_query = payments_today_query.aggregate(
                    Sum('amount_paid'))
                payments_today = payments_today_query['amount_paid__sum']
            else:
                payments_today = 0

            if len(loans_due_today_query) >= 1:
                loans_due_today_query = loans_due_today_query.aggregate(
                    Sum('remaining_amount'))
                loan_due_today = loans_due_today_query['remaining_amount__sum']
            else:
                loan_due_today = 0

            expected_date = getcurrenttime()

            all_installments = Installments.objects.filter(
                loan__status="DISBURSED", expected_date=expected_date).order_by('-id')

        else:
            branch_name = Branch.objects.get(id=current_branch)
            new_loans_today = Loans.objects.filter(
                applied_at=getcurrenttime(), borrower__branch__id=current_branch).count()

            denied_loans_today = Loans.objects.filter(
                denied_at=getcurrenttime(), borrower__branch__id=current_branch).count()

            approved_loans_today = Loans.objects.filter(
                borrower__branch__id=current_branch, approved_at=getcurrenttime()).count()

            disbursed_loans_today = Loans.objects.filter(
                borrower__branch__id=current_branch, disbursed_at=getcurrenttime()).count()

            label2 = ['NEW', 'DENIED', 'APPROVED', 'DISBURSED']
            data2 = [new_loans_today, denied_loans_today,
                     approved_loans_today, disbursed_loans_today]

            # week
            one_week_before = getcurrenttime() - timedelta(days=7)
            new_loans_this_week = Loans.objects.filter(borrower__branch__id=current_branch,
                                                       applied_at__range=[one_week_before, getcurrenttime()]).count()

            denied_loans_this_week = Loans.objects.filter(borrower__branch__id=current_branch,
                                                          denied_at__range=[one_week_before, getcurrenttime()]).count()

            approved_loans_this_week = Loans.objects.filter(borrower__branch__id=current_branch,
                                                            approved_at__range=[one_week_before, getcurrenttime()]).count()

            disbursed_loans_this_week = Loans.objects.filter(borrower__branch__id=current_branch,
                                                             disbursed_at__range=[one_week_before, getcurrenttime()]).count()

            label4 = ['NEW', 'DENIED', 'APPROVED', 'DISBURSED']
            data4 = [new_loans_this_week, denied_loans_this_week,
                     approved_loans_this_week, disbursed_loans_this_week]

            # month
            current_month = getcurrenttime().month
            new_loans_this_month = Loans.objects.filter(borrower__branch__id=current_branch,
                                                        applied_at__month=current_month).count()

            denied_loans_this_month = Loans.objects.filter(borrower__branch__id=current_branch,
                                                           denied_at__month=current_month).count()

            approved_loans_this_month = Loans.objects.filter(borrower__branch__id=current_branch,
                                                             approved_at__month=current_month).count()

            disbursed_loans_this_month = Loans.objects.filter(borrower__branch__id=current_branch,
                                                              disbursed_at__month=current_month).count()

            label5 = ['NEW', 'DENIED', 'APPROVED', 'DISBURSED']
            data5 = [new_loans_this_month, denied_loans_this_month,
                     approved_loans_this_month, disbursed_loans_this_month]

            # SECOND ANALYSIS OF NUMBER OF LOANS

            county_model = Loans.objects.filter(
                borrower__branch__id=current_branch).values_list("applied_at")

            county_count_rep = Counter([rep[0] for rep in county_model])
            county_amount_rep = {}

            for rep in county_count_rep:
                county_amount_rep[rep] = 0

            for month in county_model:
                for rep in county_amount_rep:
                    if month[0] == rep:
                        county_amount_rep[rep] += 1

            label3 = list(county_amount_rep.keys())
            data3 = list(county_amount_rep.values())

            new_loans = Borrowers.objects.filter(
                registerd_on=getcurrenttime(), branch__id=current_branch).count()
            borrowers = Borrowers.objects.filter(
                branch__id=current_branch).count()
            active_loans = Loans.objects.filter(
                status="DISBURSED", borrower__branch__id=current_branch).count()
            officers = UserProfiles.objects.filter(
                branch__id=current_branch).count()
            loans_pending_approval = Loans.objects.filter(
                status="NEW", borrower__branch__id=current_branch).count()
            loans_pending_disburse = Loans.objects.filter(
                status="APPROVED", borrower__branch__id=current_branch).count()
            loans_due_today_query = Installments.objects.filter(
                expected_date=getcurrenttime(), loan__borrower__branch__id=current_branch)

            payments_today_query = Transactions.objects.filter(
                date_of_payment=getcurrenttime(), loan__borrower__branch__id=current_branch)

            if len(payments_today_query) >= 1:
                payments_today_query = payments_today_query.aggregate(
                    Sum('amount_paid'))
                payments_today = payments_today_query['amount_paid__sum']
            else:
                payments_today = 0

            if len(loans_due_today_query) >= 1:
                loans_due_today_query = loans_due_today_query.aggregate(
                    Sum('remaining_amount'))
                loan_due_today = loans_due_today_query['remaining_amount__sum']
            else:
                loan_due_today = 0

            expected_date = getcurrenttime()
            all_installments = Installments.objects.filter(
                loan__status="DISBURSED", loan__borrower__branch=current_branch, expected_date=expected_date).order_by('-id')

    else:

        current_branch = request.user.userprofiles.branch.id
        branch_name = ''
        new_loans_today = Loans.objects.filter(
            applied_at=getcurrenttime(), borrower__branch__id=current_branch).count()

        denied_loans_today = Loans.objects.filter(
            denied_at=getcurrenttime(), borrower__branch__id=current_branch).count()

        approved_loans_today = Loans.objects.filter(
            borrower__branch__id=current_branch, approved_at=getcurrenttime()).count()

        disbursed_loans_today = Loans.objects.filter(
            borrower__branch__id=current_branch, disbursed_at=getcurrenttime()).count()

        label2 = ['NEW', 'DENIED', 'APPROVED', 'DISBURSED']
        data2 = [new_loans_today, denied_loans_today,
                 approved_loans_today, disbursed_loans_today]

        # week
        one_week_before = getcurrenttime() - timedelta(days=7)
        new_loans_this_week = Loans.objects.filter(borrower__branch__id=current_branch,
                                                   applied_at__range=[one_week_before, getcurrenttime()]).count()

        denied_loans_this_week = Loans.objects.filter(borrower__branch__id=current_branch,
                                                      denied_at__range=[one_week_before, getcurrenttime()]).count()

        approved_loans_this_week = Loans.objects.filter(borrower__branch__id=current_branch,
                                                        approved_at__range=[one_week_before, getcurrenttime()]).count()

        disbursed_loans_this_week = Loans.objects.filter(borrower__branch__id=current_branch,
                                                         disbursed_at__range=[one_week_before, getcurrenttime()]).count()

        label4 = ['NEW', 'DENIED', 'APPROVED', 'DISBURSED']
        data4 = [new_loans_this_week, denied_loans_this_week,
                 approved_loans_this_week, disbursed_loans_this_week]

        # month
        current_month = getcurrenttime().month
        new_loans_this_month = Loans.objects.filter(borrower__branch__id=current_branch,
                                                    applied_at__month=current_month).count()

        denied_loans_this_month = Loans.objects.filter(borrower__branch__id=current_branch,
                                                       denied_at__month=current_month).count()

        approved_loans_this_month = Loans.objects.filter(borrower__branch__id=current_branch,
                                                         approved_at__month=current_month).count()

        disbursed_loans_this_month = Loans.objects.filter(borrower__branch__id=current_branch,
                                                          disbursed_at__month=current_month).count()

        label5 = ['NEW', 'DENIED', 'APPROVED', 'DISBURSED']
        data5 = [new_loans_this_month, denied_loans_this_month,
                 approved_loans_this_month, disbursed_loans_this_month]

        # SECOND ANALYSIS OF NUMBER OF LOANS

        county_model = Loans.objects.filter(
            borrower__branch__id=current_branch).values_list("applied_at")

        county_count_rep = Counter([rep[0] for rep in county_model])
        county_amount_rep = {}

        for rep in county_count_rep:
            county_amount_rep[rep] = 0

        for month in county_model:
            for rep in county_amount_rep:
                if month[0] == rep:
                    county_amount_rep[rep] += 1

        label3 = list(county_amount_rep.keys())
        data3 = list(county_amount_rep.values())

        new_loans = Borrowers.objects.filter(
            registerd_on=getcurrenttime(), branch__id=current_branch).count()
        borrowers = Borrowers.objects.filter(branch__id=current_branch).count()
        active_loans = Loans.objects.filter(
            status="DISBURSED", borrower__branch__id=current_branch).count()
        officers = UserProfiles.objects.filter(
            branch__id=current_branch).count()
        loans_pending_approval = Loans.objects.filter(
            status="NEW", borrower__branch__id=current_branch).count()
        loans_pending_disburse = Loans.objects.filter(
            status="APPROVED", borrower__branch__id=current_branch).count()
        loans_due_today_query = Installments.objects.filter(
            expected_date=getcurrenttime(), loan__borrower__branch__id=current_branch)

        payments_today_query = Transactions.objects.filter(
            date_of_payment=getcurrenttime(), loan__borrower__branch__id=current_branch)

        if len(payments_today_query) >= 1:
            payments_today_query = payments_today_query.aggregate(
                Sum('amount_paid'))
            payments_today = payments_today_query['amount_paid__sum']
        else:
            payments_today = 0

        if len(loans_due_today_query) >= 1:
            loans_due_today_query = loans_due_today_query.aggregate(
                Sum('remaining_amount'))
            loan_due_today = loans_due_today_query['remaining_amount__sum']
        else:
            loan_due_today = 0

        expected_date = getcurrenttime()
        all_installments = Installments.objects.filter(
            loan__status="DISBURSED", loan__borrower__branch=current_branch, expected_date=expected_date).order_by('-id')

        # get all branches

    all_branches = Branch.objects.all()

    context = {
        'loan_due_today': loan_due_today,
        'payments_today': payments_today,
        'loans_pending_disburse': loans_pending_disburse,
        'loans_pending_approval': loans_pending_approval,
        'officers': officers,
        'all_installments': all_installments,
        'active_loans': active_loans,
        'new_loans': new_loans,
        'borrowers': borrowers,
        'label2': label2,
        'data2': data2,
        'label4': label4,
        'data4': data4,
        'label5': label5,
        'data5': data5,

        # others
        'all_branches': all_branches,
        'branch_name': branch_name,
    }

    return render(request, 'Loanapp/dashboard.html', context)


@login_required
def switch_branch(request, branch_id):
    request.session['current_branch'] = branch_id
    print(request.session['current_branch'])
    messages.success(request, 'Branch changed successfully')
    return redirect('Loanapp:index')


@login_required
def switch_branch_to_all(request):
    request.session['current_branch'] = 'all'
    messages.success(request, 'Branch changed successfully')
    return redirect('Loanapp:index')

# to register branch


@login_required
def register_branch(request):
    if request.method == 'GET':
        return render(request, 'Loanapp/register_branch.html')
    elif request.method == 'POST':
        # get relevant info
        branch_name = request.POST.get('branch_name')
        branch_location = request.POST.get('branch_location')
        address = request.POST.get('address')

        print('saving to db')
        Branch.objects.create(
            branch_name=branch_name,
            branch_location=branch_location,
            address=address,
        )
        messages.success(request, 'Branch Registered Successfully.')
        return redirect('Loanapp:index')


@login_required
def register_lead(request):
    if request.method == 'GET':
        return render(request, 'Loanapp/register_lead.html')
    elif request.method == 'POST':
        # get relevant info
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        bussiness_type = request.POST.get('bussiness_type')
        location = request.POST.get('location')

        print('saving to db')
        Leads.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            bussiness_type=bussiness_type,
            location=location,
            associated_officer=request.user
        )
        messages.success(request, 'Lead Registered Successfully.')
        return redirect('Loanapp:index')


@login_required
def list_leads(request):
    user_id = request.user.id
    associated_profile = UserProfiles.objects.get(user__id=user_id)
    role = associated_profile.role
    if role == "Admin":
        current_branch = request.session['current_branch']

        if current_branch == 'all':
            all_leads = Leads.objects.all()
        else:
            all_leads = Leads.objects.filter(
                associated_officer__userprofiles__branch__id=current_branch)
    else:
        current_user_branch = request.user.userprofiles.branch
        all_leads = Leads.objects.filter(
            associated_officer__userprofiles__branch=current_user_branch)

    context = {
        'all_leads': all_leads,

    }
    return render(request, 'Loanapp/list_leads.html', context)


@login_required
def view_branches(request):

    all_branches = Branch.objects.all()
    context = {
        'all_branches': all_branches,
    }
    return render(request, 'Loanapp/view_branches.html', context)


@login_required
def list_officers(request):
    user_id = request.user.id
    associated_profile = UserProfiles.objects.get(user__id=user_id)
    role = associated_profile.role
    if role == "Admin":
        current_branch = request.session['current_branch']

        if current_branch == 'all':
            loan_officers = UserProfiles.objects.filter(role="Loan Officer")
            loan_collection_officers = UserProfiles.objects.filter(
                role="Loan Collection Officer")
            loan_verification_officers = UserProfiles.objects.filter(
                role="Loan Verification Officer")
            admin = UserProfiles.objects.filter(
                role="Admin")
        else:
            loan_officers = UserProfiles.objects.filter(
                role="Loan Officer", branch__id=current_branch)
            loan_collection_officers = UserProfiles.objects.filter(
                role="Loan Collection Officer", branch__id=current_branch)
            loan_verification_officers = UserProfiles.objects.filter(
                role="Loan Verification Officer", branch__id=current_branch)
            admin = UserProfiles.objects.filter(
                role="Admin", branch__id=current_branch)

        context = {
            'loan_officers': loan_officers,
            'loan_collection_officers': loan_collection_officers,
            'loan_verification_officers': loan_verification_officers,
            'admin': admin,
        }
        return render(request, 'Loanapp/list_officers.html', context)

    else:
        messages.warning(request, 'Forbidden page!')
        return redirect('Loanapp:index')


@login_required
def pared_officers(request):
    user_id = request.user.id
    associated_profile = UserProfiles.objects.get(user__id=user_id)
    role = associated_profile.role
    if role == "Admin":
        current_branch = request.session['current_branch']

        if current_branch == 'all':
            all_loans = Loans.objects.all()
        else:
            all_loans = Loans.objects.filter(
                borrower__branch__id=current_branch)

        context = {
            'all_loans': all_loans,
        }
        return render(request, 'Loanapp/pared_officers.html', context)

    else:
        messages.warning(request, 'Forbidden page!')
        return redirect('Loanapp:index')


@login_required
def detail_officer(request, pk):
    officer = UserProfiles.objects.get(id=pk)
    officer_role = officer.role

    if officer_role == "Loan Officer":
        active_loans = Loans.objects.filter(
            status="DISBURSED", borrower__loan_officer=officer).order_by('-id')
        loan_history = Loans.objects.filter(borrower__loan_officer=officer).exclude(
            status="DISBURSED").order_by('-id')
        context = {
            'officer': officer,
            'active_loans': active_loans,
            'loan_history': loan_history,
        }
        return render(request, 'Loanapp/details_officers.html', context)
    elif officer_role == "Loan Collection Officer":
        active_loans = Loans.objects.filter(
            status="DISBURSED", borrower__loan_collection_officer=officer).order_by('-id')
        loan_history = Loans.objects.filter(borrower__loan_collection_officer=officer).exclude(
            status="DISBURSED").order_by('-id')
        context = {
            'officer': officer,
            'active_loans': active_loans,
            'loan_history': loan_history,
        }
        return render(request, 'Loanapp/details_officers.html', context)
    elif officer_role == "Loan Verification Officer":
        context = {
            'officer': officer,

        }
        return render(request, 'Loanapp/details_officers.html', context)
    elif officer_role == "Admin":
        context = {
            'officer': officer,

        }
        return render(request, 'Loanapp/details_officers.html', context)


# deal with borrowers
@login_required
def register_borrower(request):
    if request.method == 'GET':
        form = BorrowersProfile(request.POST or None)
        context = {
            'form': form,
        }
        return render(request, 'Loanapp/register_borrower.html', context)
    else:

        form = BorrowersProfile(request.POST or None)
        # logic to fetch data from post
        branch = request.POST.get('branch')
        disbursment_number = request.POST.get('disbursment_number')
        national_id = request.POST.get('national_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        dob = request.POST.get('dob')
        nickname = request.POST.get('nickname')
        phone_number = request.POST.get('phone_number')
        alt_phone_number = request.POST.get('alt_phone_number')
        gender = request.POST.get('gender')
        marital_status = request.POST.get('marital_status')
        next_of_kin_name = request.POST.get('next_of_kin_name')
        next_of_kin_id = request.POST.get('next_of_kin_id')
        next_of_kin_relationship = request.POST.get(
            'next_of_kin_relationship')
        address = request.POST.get('address')
        non_schooling = request.POST.get('non_schooling')
        primary_dependants = request.POST.get('primary_dependants')
        secondary_dependants = request.POST.get('secondary_dependants')
        tertiary_dependants = request.POST.get('tertiary_dependants')
        working_status = request.POST.get('working_status')
        bussiness_address = request.POST.get('bussiness_address')
        bussiness_location = request.POST.get('bussiness_location')
        residence_town = request.POST.get('residence_town')
        estimate_building = request.POST.get('estimate_building')
        street_house_number = request.POST.get('street_house_number')
        bussiness_age = request.POST.get('bussiness_age')
        bussiness_type = request.POST.get('bussiness_type')
        loan_security = request.POST.get('loan_security')
        loan_officer = request.POST.get('loan_officer')
        loan_collection_officer = request.POST.get(
            'loan_collection_officer')
        good_day = request.POST.get('good_day')
        bad_day = request.POST.get('bad_day')
        days_per_week = request.POST.get('days_per_week')
        stock_purchase = request.POST.get('stock_purchase')
        transport = request.POST.get('transport')
        rent = request.POST.get('rent')
        salary = request.POST.get('salary')
        other_expenses = request.POST.get('other_expenses')
        # images
        front_id_image = request.FILES['front_id_image']
        try:
            back_id_image = request.FILES['back_id_image']
        except:
            back_id_image = ''
        try:
            files = request.FILES['files']
        except:
            files = ''

        # map
        map_address = request.POST.get('map_address')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        # check if user with this Id number exists.

        all_borrowers = Borrowers.objects.all()
        for each_borrower in all_borrowers:
            if each_borrower.national_id == national_id:
                messages.warning(
                    request, 'Sorry, borrower with this Id number is already registered.')
                context = {
                    'form': form,
                }
                return render(request, 'Loanapp/register_borrower.html', context)

        # get instance
        branch = Branch.objects.get(id=branch)
        loan_officer = UserProfiles.objects.get(id=loan_officer)
        loan_collection_officer = UserProfiles.objects.get(
            id=loan_collection_officer)

        # generate Walaka Id
        branch_name = branch.branch_name
        first_letter_of_branch = branch_name[0]

        # Generate random number between 1 and 100000
        # rand_num = random.randrange(1, 100000)
        # change int to str
        # rand_num = str(rand_num)

        count_all_borrower = Borrowers.objects.all()

        if len(count_all_borrower) > 0:
            # get last record
            last = Borrowers.objects.all().last()
            last_gen_num = last.gen_num
            new_gen_num = last_gen_num + 1
        else:
            new_gen_num = 1

        # join rand number and integer
        # if branch_name == ""
        final_walaka_id = first_letter_of_branch + \
            str(branch.id) + str(0) + str(0) + str(new_gen_num)
        # check to see if this id exists already.
        # for each_borrower in all_borrowers:
        #     if each_borrower.walaka_id == final_walaka_id:
        #         rand_num = str(rand_num)
        #         final_walaka_id = first_letter_of_branch + rand_num
        #     else:
        #         pass

        # save to db.

        try:

            borrower = Borrowers.objects.create(
                branch=branch,
                walaka_id=final_walaka_id,
                gen_num=new_gen_num,
                disbursment_number=disbursment_number,
                national_id=national_id,
                first_name=first_name,
                last_name=last_name,
                nickname=nickname,
                phone_number=phone_number,
                alt_phone_number=alt_phone_number,
                gender=gender,
                marital_status=marital_status,
                next_of_kin_name=next_of_kin_name,
                next_of_kin_id=next_of_kin_id,
                next_of_kin_relationship=next_of_kin_relationship,
                dob=dob,
                address=address,
                map_address=map_address,
                latitude=latitude,
                longitude=longitude,
                non_schooling=non_schooling,
                primary_dependants=primary_dependants,
                secondary_dependants=secondary_dependants,
                tertiary_dependants=tertiary_dependants,
                working_status=working_status,
                bussiness_address=bussiness_address,
                bussiness_location=bussiness_location,
                residence_town=residence_town,
                estimate_building=estimate_building,
                street_house_number=street_house_number,
                bussiness_age=bussiness_age,
                bussiness_type=bussiness_type,
                loan_security=loan_security,
                # error here
                loan_officer=loan_officer,
                loan_collection_officer=loan_collection_officer,
                good_day=good_day,
                bad_day=bad_day,
                days_per_week=days_per_week,
                stock_purchase=stock_purchase,
                transport=transport,
                rent=rent,
                salary=salary,
                other_expenses=other_expenses,
                front_id_image=front_id_image,
                back_id_image=back_id_image,
                files=files,
            )
            borrower_id = borrower.pk
            borrower = Borrowers.objects.get(pk=borrower_id)
            context = {
                'borrower': borrower,
            }
            messages.info(
                request, 'Borrower basic info captured. Please provide the additional info below')
            return redirect('Loanapp:additional_info', pk=borrower_id)
        except:
            messages.warning(
                request, 'An error occured while registering this user.')
            return redirect('Loanapp:index')


@login_required
def list_borrowers(request):
    user_id = request.user.id
    current_user_branch = request.user.userprofiles.branch
    associated_profile = UserProfiles.objects.get(user__id=user_id)
    role = associated_profile.role
    if role == "Admin":
        current_branch = request.session['current_branch']

        if current_branch == 'all':
            all_borrowers = Borrowers.objects.all().order_by('-id')
        else:
            all_borrowers = Borrowers.objects.filter(
                branch__id=current_branch).order_by('-id')

        context = {
            'all_borrowers': all_borrowers,
        }
        return render(request, 'Loanapp/list_borrowers.html', context)
    else:
        all_borrowers = Borrowers.objects.filter(
            branch=current_user_branch).order_by('-id')
        context = {
            'all_borrowers': all_borrowers,
        }
        return render(request, 'Loanapp/list_borrowers.html', context)


@login_required
def detail_borrower(request, pk):
    user_id = request.user.id
    associated_profile = UserProfiles.objects.get(user__id=user_id)
    role = associated_profile.role
    borrower = Borrowers.objects.get(id=pk)

    # print(request.user.userprofiles.role)

    totaldependants = int(borrower.non_schooling) + \
        int(borrower.primary_dependants) + int(borrower.secondary_dependants) + \
        int(borrower.tertiary_dependants)

    var1 = (int(borrower.good_day) + int(borrower.bad_day))/2
    var2 = var1 * int(borrower.days_per_week)
    total_income = var2 * 4

    print(total_income)

    total_expense = int(borrower.stock_purchase) + int(borrower.transport) + int(borrower.rent) + \
        int(borrower.salary) + int(borrower.other_expenses)
    print(total_expense)

    total_bussiness_profitability = total_income - total_expense

    # get all guarantors associated
    all_associated_guarantors = Guarantors.objects.filter(borrower__id=pk)
    all_associated_referee = Referees.objects.filter(borrower__id=pk)
    all_associated_assets = Assets.objects.filter(borrower__id=pk)
    all_associated_avatars = AvatarImages.objects.filter(borrower__id=pk)
    all_loan_history = Loans.objects.filter(
        borrower__id=pk).order_by('-applied_at')
    active_loan = Loans.objects.filter(borrower__id=pk, status="DISBURSED")

    all_borrower_notes = BorrowerNotes.objects.filter(borrower__id=pk)

    context = {
        'borrower': borrower,
        'role': role,
        'totaldependants': totaldependants,
        'total_bussiness_profitability': total_bussiness_profitability,
        'all_associated_guarantors': all_associated_guarantors,
        'all_associated_referee': all_associated_referee,
        'all_associated_assets': all_associated_assets,
        'all_associated_avatars': all_associated_avatars,
        'all_loan_history': all_loan_history,
        'active_loan': active_loan,
        'all_borrower_notes': all_borrower_notes,
    }
    return render(request, 'Loanapp/detail_borrower.html', context)


@login_required
def additional_info(request, pk):
    try:
        borrower = Borrowers.objects.get(id=pk)
        if request.method == "GET":
            all_associated_guarantors = Guarantors.objects.filter(
                borrower__id=pk)
            all_associated_referee = Referees.objects.filter(borrower__id=pk)
            all_associated_assets = Assets.objects.filter(borrower__id=pk)
            context = {
                'borrower': borrower,
                'all_associated_guarantors': all_associated_guarantors,
                'all_associated_referee': all_associated_referee,
                'all_associated_assets': all_associated_assets,
            }
            return render(request, 'Loanapp/additional_info.html', context)
        else:
            pass
    except ObjectDoesNotExist:
        messages.warning(
            request, 'Sorry, Borrower with this Id does Not exist in our systems')


@login_required
def create_guarantor(request, pk):
    try:
        borrower = Borrowers.objects.get(id=pk)
        if request.method == "POST":
            guarantors_full_name = request.POST.get('guarantors_full_name')
            guarantors_contact = request.POST.get('guarantors_contact')
            guarantors_relation = request.POST.get('guarantors_relation')

            Guarantors.objects.create(
                borrower=borrower,
                guarantors_full_name=guarantors_full_name,
                guarantors_contact=guarantors_contact,
                guarantors_relation=guarantors_relation
            )
            messages.success(request, 'Guarantor created successfully')
            return redirect('Loanapp:detail_borrower', pk=pk)

    except ObjectDoesNotExist:
        messages.warning(
            request, 'Sorry, Borrower with this Id does Not exist in our systems')


@login_required
def create_guarantor_ajax(request, pk):
    try:
        borrower = Borrowers.objects.get(id=pk)
        if request.method == "POST":
            guarantors_full_name = request.POST.get('guarantors_full_name')
            guarantors_contact = request.POST.get('guarantors_contact')
            guarantors_relation = request.POST.get('guarantors_relation')

            record_count = Referees.objects.filter(borrower__id=pk).count()
            recordno = record_count + 1

            new_guarantor = Guarantors.objects.create(
                borrower=borrower,
                guarantors_full_name=guarantors_full_name,
                guarantors_contact=guarantors_contact,
                guarantors_relation=guarantors_relation
            )
            response_data = {}
            response_data['guarantors_name'] = new_guarantor.guarantors_full_name
            response_data['guarantors_contact'] = new_guarantor.guarantors_contact
            response_data['relation'] = new_guarantor.guarantors_relation
            response_data['record'] = recordno

            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json"
            )

    except ObjectDoesNotExist:
        messages.warning(
            request, 'Sorry, Borrower with this Id does Not exist in our systems')


@login_required
def create_referee(request, pk):
    try:
        borrower = Borrowers.objects.get(id=pk)
        if request.method == "POST":
            referee_full_name = request.POST.get('referee_full_name')
            referee_contact = request.POST.get('referee_contact')
            referee_relation = request.POST.get('referee_relation')

            Referees.objects.create(
                borrower=borrower,
                referee_full_name=referee_full_name,
                referee_contact=referee_contact,
                referee_relation=referee_relation
            )
            messages.success(request, 'Referee created successfully')
            return redirect('Loanapp:detail_borrower', pk=pk)

    except ObjectDoesNotExist:
        messages.warning(
            request, 'Sorry, Borrower with this Id does Not exist in our systems')


@login_required
def create_referee_ajax(request, pk):
    try:
        borrower = Borrowers.objects.get(id=pk)
        if request.method == "POST":
            referee_full_name = request.POST.get('referee_full_name')
            referee_contact = request.POST.get('referee_contact')
            referee_relation = request.POST.get('referee_relation')

            record_count = Guarantors.objects.filter(borrower__id=pk).count()
            recordno = record_count + 1

            new_referee = Referees.objects.create(
                borrower=borrower,
                referee_full_name=referee_full_name,
                referee_contact=referee_contact,
                referee_relation=referee_relation
            )
            response_data = {}
            response_data['referee_full_name'] = new_referee.referee_full_name
            response_data['referee_contact'] = new_referee.referee_contact
            response_data['referee_relation'] = new_referee.referee_relation
            response_data['record'] = recordno
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json"
            )

    except ObjectDoesNotExist:
        messages.warning(
            request, 'Sorry, Borrower with this Id does Not exist in our systems')


@login_required
def create_asset(request, pk):
    try:
        borrower = Borrowers.objects.get(id=pk)
        if request.method == "POST":
            asset_full_name = request.POST.get('asset_full_name')
            value = request.POST.get('value')
            description = request.POST.get('description')

            Assets.objects.create(
                borrower=borrower,
                asset_full_name=asset_full_name,
                value=value,
                description=description
            )
            messages.success(request, 'Asset created successfully')
            return redirect('Loanapp:detail_borrower', pk=pk)

    except ObjectDoesNotExist:
        messages.warning(
            request, 'Sorry, Borrower with this Id does Not exist in our systems')


@login_required
def create_asset_ajax(request, pk):
    try:
        borrower = Borrowers.objects.get(id=pk)
        if request.method == "POST":
            asset_full_name = request.POST.get('asset_full_name')
            value = request.POST.get('value')
            description = request.POST.get('description')

            record_count = Guarantors.objects.filter(borrower__id=pk).count()
            recordno = record_count + 1

            new_asset = Assets.objects.create(
                borrower=borrower,
                asset_full_name=asset_full_name,
                value=value,
                description=description
            )
            response_data = {}
            response_data['asset_full_name'] = new_asset.asset_full_name
            response_data['value'] = new_asset.value
            response_data['description'] = new_asset.description
            response_data['record'] = recordno
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json"
            )

    except ObjectDoesNotExist:
        messages.warning(
            request, 'Sorry, Borrower with this Id does Not exist in our systems')


@login_required
def save_avatars(request, pk):
    try:
        borrower = Borrowers.objects.get(id=pk)
        if request.method == 'POST':
            avatars = request.FILES.getlist('avatars')
            for avatar in avatars:
                AvatarImages.objects.create(
                    borrower=borrower,
                    image=avatar,
                )
            messages.success(request, 'Profile Saved successfully')
            return redirect('Loanapp:detail_borrower', pk=pk)
    except:
        messages.warning(
            request, 'Sorry, an error occured please contact the administrator.')
        return redirect('Loanapp:index')


@login_required
def apply_for_loan(request):
    return render(request, 'Loanapp/apply_for_loan_validator.html')
    # register user


@login_required
def perform_loan_validation(request):
    if request.method == "POST":
        id_number = request.POST.get('id_number')
        print(id_number)
        # if borrower has an active loan.
        find_borrower = Borrowers.objects.filter(national_id=id_number)
        if len(find_borrower) == 1:
            active_loan = Loans.objects.filter(borrower__national_id=id_number).filter(
                Q(status="NEW") | Q(status="APPROVED") | Q(status="DISBURSED"))
            if len(active_loan) >= 1:
                messages.warning(
                    request, 'Sorry, This borrower has an active Loan.If not, the loan applied is still under review. Contact the Loan officer in charge.')
                return redirect('Loanapp:apply_for_loan')
            else:
                messages.success(
                    request, 'Borrower viable for a loan. Kindly fill in the form below.')
                pk = find_borrower[0].id
                return redirect('Loanapp:apply_loan_form', pk=pk)
        else:
            messages.warning(
                request, 'Warning! Borrower with this Id number Does not exist in the system.')
            return redirect('Loanapp:apply_for_loan')


def getcurrenttime():
    now_date = date.today()
    return now_date


@login_required
def apply_loan_form(request, pk):
    if request.method == 'GET':
        try:
            borrower = Borrowers.objects.get(id=pk)
            active_loan = Loans.objects.filter(borrower__id=pk).filter(
                Q(status="NEW") | Q(status="APPROVED") | Q(status="DISBURSED"))
            if len(active_loan) >= 1:
                messages.warning(
                    request, 'Sorry, This borrower has an active Loan. If not, the loan applied is still under review. Contact the Loan officer incharge')
                return redirect('Loanapp:index')
            else:
                all_associated_avatars = AvatarImages.objects.filter(
                    borrower__id=pk)

                context = {
                    'borrower': borrower,
                    'all_associated_avatars': all_associated_avatars,
                }
                return render(request, 'Loanapp/apply_loan_form.html', context)
        except ObjectDoesNotExist:
            messages.warning(
                request, 'Sorry, borrower with this Id number does not exist')
            return redirect('Loanapp:index')
    else:

        # get data from the form
        loan_type = request.POST.get('loan_type')
        expected_amount = request.POST.get('expected_amount')
        period = request.POST.get('period')
        plan = request.POST.get('plan')
        loan_purpose1 = request.POST.get('loan_purpose1')
        loan_purpose2 = request.POST.get('loan_purpose2')
        loan_purpose3 = request.POST.get('loan_purpose3')
        loan_purpose4 = request.POST.get('loan_purpose4')

        borrower = Borrowers.objects.get(id=pk)

        # get loan_percentage
        if int(period) <= 12:
            loan_percentage = 12
        elif int(period) > 12:
            loan_percentage = period

        # get total_loan
        interest = int(expected_amount) * (int(loan_percentage)/100)

        total_loan = int(expected_amount) + int(interest)

        # create record
        Loans.objects.create(
            borrower=borrower,
            loan_type=loan_type,
            expected_amount=int(expected_amount),
            loan_percentage=int(loan_percentage),
            period=int(period),
            total_loan=int(total_loan),
            payment_type=plan,
            loan_purpose1=loan_purpose1,
            loan_purpose2=loan_purpose2,
            loan_purpose3=loan_purpose3,
            loan_purpose4=loan_purpose4,
            status="NEW",
            applied_at=getcurrenttime()
        )
        messages.success(
            request, 'Loan application submited successfully. Kindly wait as the loan is being verified by our officers.')
        return redirect('Loanapp:index')


@login_required
def approve_loan_list(request):
    if request.user.userprofiles.role == 'Admin' or request.user.userprofiles.role == 'Loan Verification Officer':
        current_user_branch = request.user.userprofiles.branch
        if request.user.userprofiles.role == 'Admin':
            current_branch = request.session['current_branch']

            if current_branch == 'all':
                all_loans = Loans.objects.filter(
                    status="NEW").order_by('-applied_at')
            else:
                all_loans = Loans.objects.filter(
                    status="NEW", borrower__branch__id=current_branch).order_by('-applied_at')

            context = {
                "all_loans": all_loans,
            }
            return render(request, 'Loanapp/approve_loan_list.html', context)
        else:
            all_loans = Loans.objects.filter(
                status="NEW", borrower__branch=current_user_branch).order_by('-applied_at')
            context = {
                "all_loans": all_loans,
            }
            return render(request, 'Loanapp/approve_loan_list.html', context)
    else:
        messages.warning(
            request, 'Sorry you are not allowed to be in this page. fuck off.')
        return redirect('Loanapp:index')


@login_required
def approve_loan_details(request, pk):
    loan = Loans.objects.get(id=pk)
    borrower = loan.borrower
    borrower_id = loan.borrower.id
    role = request.user.userprofiles.role
    totaldependants = int(borrower.non_schooling) + \
        int(borrower.primary_dependants) + int(borrower.secondary_dependants) + \
        int(borrower.tertiary_dependants)
    var1 = (int(borrower.good_day) + int(borrower.bad_day))/2
    var2 = var1 * int(borrower.days_per_week)
    total_income = var2 * 4

    total_expense = int(borrower.stock_purchase) + int(borrower.transport) + int(borrower.rent) + \
        int(borrower.salary) + int(borrower.other_expenses)
    total_bussiness_profitability = total_income - total_expense

    all_associated_referee = Referees.objects.filter(borrower__id=borrower_id)
    all_associated_guarantors = Guarantors.objects.filter(
        borrower__id=borrower_id)
    all_associated_assets = Assets.objects.filter(borrower__id=borrower_id)
    all_associated_avatars = AvatarImages.objects.filter(
        borrower__id=borrower_id)
    all_loan_history = Loans.objects.filter(
        borrower__id=pk).order_by('-applied_at')
    active_loan = Loans.objects.filter(borrower__id=pk, status="DISBURSED")

    context = {
        'loan': loan,
        'role': role,
        'borrower': borrower,
        'totaldependants': totaldependants,
        'total_bussiness_profitability': total_bussiness_profitability,

        'all_associated_guarantors': all_associated_guarantors,
        'all_associated_referee': all_associated_referee,
        'all_associated_assets': all_associated_assets,
        'all_associated_avatars': all_associated_avatars,

    }
    return render(request, 'Loanapp/approve_loan_details.html', context)


@login_required
def change_to_approved(request, pk):
    loan = Loans.objects.get(id=pk)
    loan.status = "APPROVED"
    loan.approved_at = getcurrenttime()
    loan.approved_by = request.user
    loan.save()
    messages.success(
        request, 'Loan Approved successfull. Consult with Loan officer for disbursement.')
    return redirect('Loanapp:index')


@login_required
def change_to_denied(request, pk):
    loan = Loans.objects.get(id=pk)
    loan.status = "DENIED"
    loan.denied_at = getcurrenttime()
    loan.denied_by = request.user
    loan.save()
    messages.success(
        request, 'Loan Denied successfull.')
    return redirect('Loanapp:index')


@login_required
def pay_membershipfee(request, pk, loan_id):
    borrower = Borrowers.objects.get(id=pk)
    borrower.paid_membership_fee = True
    borrower.save()

    MembershipFees.objects.create(
        borrower=borrower
    )
    messages.success(
        request, 'Membership Fee paid successfully.')
    return redirect('Loanapp:disburse_loan_details', pk=loan_id)


@login_required
def disburse_list(request):
    current_user_branch = request.user.userprofiles.branch
    if request.user.userprofiles.role == 'Admin':
        current_branch = request.session['current_branch']

        if current_branch == 'all':
            all_loans = Loans.objects.filter(status="APPROVED")
        else:
            all_loans = Loans.objects.filter(
                status="APPROVED", borrower__branch__id=current_branch)

        context = {
            'all_loans': all_loans,
        }
        return render(request, 'Loanapp/disburse_list.html', context)
    else:
        all_loans = Loans.objects.filter(
            status="APPROVED", borrower__branch=current_user_branch)
        context = {
            'all_loans': all_loans,
        }
        return render(request, 'Loanapp/disburse_list.html', context)


@login_required
def disburse_loan_details(request, pk):
    loan = Loans.objects.get(id=pk)
    loan_status = loan.status

    if loan_status != "APPROVED":
        messages.warning(
            request, 'Invalid Access!')
        return redirect('Loanapp:index')

    borrower = loan.borrower
    borrower_id = loan.borrower.id
    borrower_membership_status = loan.borrower.paid_membership_fee
    role = request.user.userprofiles.role
    totaldependants = int(borrower.non_schooling) + \
        int(borrower.primary_dependants) + int(borrower.secondary_dependants) + \
        int(borrower.tertiary_dependants)
    var1 = (int(borrower.good_day) + int(borrower.bad_day))/2
    var2 = var1 * int(borrower.days_per_week)
    total_income = var2 * 4

    total_expense = int(borrower.stock_purchase) + int(borrower.transport) + int(borrower.rent) + \
        int(borrower.salary) + int(borrower.other_expenses)
    total_bussiness_profitability = total_income - total_expense

    all_associated_referee = Referees.objects.filter(borrower__id=borrower_id)
    all_associated_guarantors = Guarantors.objects.filter(
        borrower__id=borrower_id)
    all_associated_assets = Assets.objects.filter(borrower__id=borrower_id)
    all_associated_avatars = AvatarImages.objects.filter(
        borrower__id=borrower_id)
    all_loan_history = Loans.objects.filter(
        borrower__id=pk).order_by('-applied_at')
    active_loan = Loans.objects.filter(borrower__id=pk, status="DISBURSED")

    context = {
        'loan': loan,
        'role': role,
        'borrower': borrower,
        'totaldependants': totaldependants,
        'total_bussiness_profitability': total_bussiness_profitability,

        'all_associated_guarantors': all_associated_guarantors,
        'all_associated_referee': all_associated_referee,
        'all_associated_assets': all_associated_assets,
        'all_associated_avatars': all_associated_avatars,
        'borrower_membership_status': borrower_membership_status,

    }
    return render(request, 'Loanapp/disburse_loan.html', context)


# This function right here is a pain in the ass.
@login_required
def change_to_disbursed(request, pk):
    loan = Loans.objects.get(id=pk)
    borrower_paid_membership = loan.borrower.paid_membership_fee
    if borrower_paid_membership == False:
        messages.warning(
            request, 'Membership fee of Ksh 500 must be paid before loan is disbursed.')
        return redirect('Loanapp:index')
    else:
        # create installment schedule
        payment_plan = loan.payment_type
        period = loan.period
        total_loan = loan.total_loan

        # calculate installments
        if payment_plan == "Daily":
            number_of_installments = int(period)

        elif payment_plan == "Weekly":
            number_of_installments = math.floor(int(period) / 7)

        elif payment_plan == "Monthly":
            number_of_installments = math.ceil(int(period) / 30)

        # now we have the number of installments.

        loan.status = "DISBURSED"
        loan.disbursed_at = getcurrenttime()
        loan.disbursed_by = request.user
        loan.save()

        disbursment_date = loan.disbursed_at
        installment_expected_amount = total_loan/number_of_installments
        installment_expected_amount = math.ceil(installment_expected_amount)
        one_week_past_disbursement_date = disbursment_date + timedelta(days=7)

        i = 1

        loan.startpayment_at = one_week_past_disbursement_date
        loan.endpayment_at = disbursment_date + timedelta(days=30)
        loan.run_penalty_date = disbursment_date + timedelta(days=30)
        loan.save()

        today_date = getcurrenttime()
        startpaymentdate = loan.disbursed_at
        principal_amount = loan.expected_amount
        period = loan.period

        # calculate balance today
        difference_in_time = today_date - startpaymentdate
        difference_in_time = difference_in_time.days
        print(difference_in_time)

        if int(period) <= 12:
            # calculate interest
            interest = principal_amount * 0.12
        elif int(period) > 12:
            interest = principal_amount * (int(period)/100)

        balance_today = principal_amount + interest
        loan.balance_today = balance_today
        loan.amount_remain = balance_today
        loan.amount_paid = 0
        loan.save()

        print(balance_today)

        expected_date = one_week_past_disbursement_date

        for each in range(0, number_of_installments):
            Installments.objects.create(
                loan=loan,
                installment_number=i,
                expected_amount=installment_expected_amount,
                remaining_amount=installment_expected_amount,
                expected_date=expected_date
            )

            if payment_plan == "Daily":
                expected_date = expected_date + timedelta(days=1)

            elif payment_plan == "Weekly":
                expected_date = expected_date + timedelta(days=7)

            elif payment_plan == "Monthly":
                expected_date = expected_date + timedelta(days=30)

            i += 1

        #

        messages.success(
            request, 'Loan Disbursed Successfull.')
        return redirect('Loanapp:index')


@login_required
def loan_list(request):
    current_user_branch = request.user.userprofiles.branch

    if request.user.userprofiles.role == 'Admin':
        current_branch = request.session['current_branch']

        if current_branch == 'all':
            # superuser sees all
            active_loans = Loans.objects.filter(
                status="DISBURSED").order_by('-id')
            loan_history = Loans.objects.all().exclude(status="DISBURSED").order_by('-id')
        else:  # superuser sees all
            active_loans = Loans.objects.filter(
                status="DISBURSED", borrower__branch__id=current_branch).order_by('-id')
            loan_history = Loans.objects.all().exclude(
                status="DISBURSED", borrower__branch__id=current_branch).order_by('-id')
        context = {
            'active_loans': active_loans,
            'loan_history': loan_history,
        }
        return render(request, 'Loanapp/loan_list.html', context)
    else:
        active_loans = Loans.objects.filter(
            status="DISBURSED", borrower__branch=current_user_branch).order_by('-id')
        loan_history = Loans.objects.filter(
            borrower__branch=current_user_branch).exclude(status="DISBURSED").order_by('-id')
        context = {
            'active_loans': active_loans,
            'loan_history': loan_history,
        }
        return render(request, 'Loanapp/loan_list.html', context)


@login_required
def loan_history(request):
    current_user_branch = request.user.userprofiles.branch
    if request.user.userprofiles.role == 'Admin':
        current_branch = request.session['current_branch']

        if current_branch == 'all':
            # superuser sees all
            active_loans = Loans.objects.filter(
                status="DISBURSED").order_by('-id')
            loan_history = Loans.objects.all().exclude(status="DISBURSED").order_by('-id')
        else:  # superuser sees all
            active_loans = Loans.objects.filter(
                status="DISBURSED", borrower__branch__id=current_branch).order_by('-id')
            loan_history = Loans.objects.all().exclude(
                status="DISBURSED", borrower__branch__id=current_branch).order_by('-id')
        context = {
            'active_loans': active_loans,
            'loan_history': loan_history,
        }
        return render(request, 'Loanapp/loan_history.html', context)
    else:
        active_loans = Loans.objects.filter(
            status="DISBURSED", borrower__branch=current_user_branch).order_by('-id')
        loan_history = Loans.objects.filter(
            borrower__branch=current_user_branch).exclude(status="DISBURSED").order_by('-id')
        context = {
            'active_loans': active_loans,
            'loan_history': loan_history,
        }
        return render(request, 'Loanapp/loan_history.html', context)


@login_required
def loan_detail(request, pk):
    loan = Loans.objects.get(id=pk)
    remaining_amount = loan.amount_remain

    loan_interst = loan.total_loan - loan.expected_amount
    if loan.status == "DISBURSED" and remaining_amount <= 0:
        loan.status = "FULLY_PAID"
        loan.fully_paid_on = getcurrenttime()
        loan.save()

    if loan.status == "FULLY_PAID" and remaining_amount < 0:
        excess_overpayments = 0 - remaining_amount
        LoanOverpayments.objects.create(
            borrower=loan.borrower,
            amount_paid=excess_overpayments,
            date_of_payment=getcurrenttime()
        )

        loan.amount_remain = 0
        loan.save()
    borrower = loan.borrower
    current_user_branch = request.user.userprofiles.branch
    loan_members_branch = loan.borrower.branch
    all_associated_referee = Referees.objects.filter(borrower=borrower)
    all_associated_guarantors = Guarantors.objects.filter(
        borrower=borrower)
    all_associated_assets = Assets.objects.filter(borrower=borrower)

    totaldependants = int(borrower.non_schooling) + \
        int(borrower.primary_dependants) + int(borrower.secondary_dependants) + \
        int(borrower.tertiary_dependants)
    var1 = (int(borrower.good_day) + int(borrower.bad_day))/2
    var2 = var1 * int(borrower.days_per_week)
    total_income = var2 * 4

    total_expense = int(borrower.stock_purchase) + int(borrower.transport) + int(borrower.rent) + \
        int(borrower.salary) + int(borrower.other_expenses)
    total_bussiness_profitability = total_income - total_expense
    expected_payment_schedule = Installments.objects.filter(loan=loan)

    # calc loan today
    today_date = getcurrenttime()
    startpaymentdate = loan.disbursed_at
    principal_amount = loan.expected_amount

    # calc balance
    all_unpaid_installments = Installments.objects.filter(
        loan=loan, fully_paid=False)
    if len(all_unpaid_installments) >= 1:
        unpaid_sum = all_unpaid_installments.aggregate(Sum('remaining_amount'))
        unpaid_sum = unpaid_sum['remaining_amount__sum']
    else:
        unpaid_sum = 0
    # calculate balance today
    if loan.status == "DISBURSED" or loan.status == "FULLY_PAID":
        difference_in_time = today_date - startpaymentdate
        difference_in_time = difference_in_time.days
        amount_paid = loan.amount_paid
        if difference_in_time <= 12:
            # calculate interest
            interest = principal_amount * 0.12
        elif difference_in_time > 12:
            interest = principal_amount * (int(difference_in_time)/100)

        balance_today = principal_amount + interest
        loan.balance_today = balance_today - amount_paid
        loan.save()
    else:
        difference_in_time = 0

    # get related installments
    all_installments = Installments.objects.filter(
        loan=loan).order_by('expected_date')
    all_transactions = Transactions.objects.filter(loan=loan)

    all_repayments = LoanRepayment.objects.filter(loan=loan)
    all_loan_history = Loans.objects.filter(
        borrower=borrower).order_by('-applied_at')
    active_loan = Loans.objects.filter(borrower=borrower, status="DISBURSED")
    all_loan_notes = LoanNotes.objects.filter(loan=loan).order_by('-id')

    if request.user.userprofiles.role == 'Admin':
        context = {
            'loan': loan,
            'borrower': borrower,
            'all_associated_guarantors': all_associated_guarantors,
            'all_associated_referee': all_associated_referee,
            'all_associated_assets': all_associated_assets,
            'totaldependants': totaldependants,
            'total_bussiness_profitability': total_bussiness_profitability,
            'expected_payment_schedule': expected_payment_schedule,
            'all_installments': all_installments,
            'all_repayments': all_repayments,
            'all_loan_history': all_loan_history,
            'active_loan': active_loan,
            'all_transactions': all_transactions,
            'all_loan_notes': all_loan_notes,
            'loan_interst': loan_interst,
            'unpaid_sum': unpaid_sum,
        }
        return render(request, 'Loanapp/loan_detail.html', context)
    else:
        if current_user_branch != loan_members_branch:
            messages.warning(
                request, 'Unauthorized access')
            return redirect('Loanapp:index')
        else:
            context = {
                'loan': loan,
                'borrower': borrower,
                'all_associated_guarantors': all_associated_guarantors,
                'all_associated_referee': all_associated_referee,
                'all_associated_assets': all_associated_assets,
                'totaldependants': totaldependants,
                'total_bussiness_profitability': total_bussiness_profitability,
                'expected_payment_schedule': expected_payment_schedule,
                'all_installments': all_installments,
                'all_repayments': all_repayments,
                'all_loan_history': all_loan_history,
                'all_transactions': all_transactions,
                'active_loan': active_loan,
                'all_loan_notes': all_loan_notes,
                'loan_interst': loan_interst,
                'unpaid_sum': unpaid_sum,
            }
            return render(request, 'Loanapp/loan_detail.html', context)


# loan repayment
@login_required
def loan_repay(request):
    def save_loan(loan, only_installment, amount):
        LoanRepayment.objects.create(
            loan=loan,
            tied_installment=only_installment,
            amount_paid=amount,
            date_of_payment=getcurrenttime()
        )

    if request.method == 'GET':
        return render(request, 'Loanapp/loan_repay.html')
    elif request.method == 'POST':
        print(request.POST)
        id_number = request.POST.get('id_number')
        amount = request.POST.get('amount')

        # get associated loan
        all_active_loans = Loans.objects.filter(
            status="DISBURSED")

        print(all_active_loans)

        associated_user_found = False

        for each_loan in all_active_loans:
            print(each_loan.borrower.national_id)
            print(id_number)

            if each_loan.borrower.national_id == id_number:
                associated_user_found = True
            else:
                associated_user_found = False

        if associated_user_found == False:
            messages.warning(
                request, 'Sorry, No loan associated to this borrower found.')
            return redirect('Loanapp:index')
        else:
            print('found record')
            loan = Loans.objects.get(
                borrower__national_id=id_number, status="DISBURSED")

            Transactions.objects.create(
                loan=loan,
                amount_paid=amount,
                date_of_payment=getcurrenttime()
            )

            # start evaluating installments and everything
            all_related_installments = Installments.objects.filter(
                loan=loan, fully_paid=False).order_by('expected_date')

            all_installment_id = []

            for installment in all_related_installments:
                installment_id = installment.id
                all_installment_id.append(installment_id)

            if len(all_installment_id) > 1:

                # get earliest installments
                earliest_installment = min(all_installment_id)
                least_installment = Installments.objects.get(
                    id=earliest_installment)

                # get outstanding balance of least installment
                least_installment_amount = least_installment.remaining_amount

                if int(amount) > least_installment_amount:
                    # overflow
                    remaining_amount_after_removing_least_installment_amount = int(
                        amount) - least_installment_amount

                    least_installment.remaining_amount = 0
                    least_installment.fully_paid = True
                    least_installment.save()

                    save_loan(loan, least_installment,
                              least_installment_amount)

                    loan.amount_paid += int(least_installment_amount)
                    loan.amount_remain -= int(least_installment_amount)
                    loan.save()

                    all_installment_id.remove(earliest_installment)

                    print(all_installment_id)

                    # get least of the now all_installments

                    new_earliest_installment_id = min(all_installment_id)

                    # get instance of the same

                    new_earliest_installment = Installments.objects.get(
                        id=new_earliest_installment_id)

                    # get expected amount of least installment
                    new_earliest_installment_expected_amount = new_earliest_installment.expected_amount

                    number_of_overflows = int(math.floor(
                        remaining_amount_after_removing_least_installment_amount) / int(new_earliest_installment_expected_amount))

                    remaining_modulus = int(remaining_amount_after_removing_least_installment_amount) % int(
                        new_earliest_installment_expected_amount)

                    print('remaining modulus ' + str(remaining_modulus))
                    print('Number of overflows ' + str(number_of_overflows))

                    length_of_remaining_installments = len(all_installment_id)

                    print('number of remainign installments ' +
                          str(length_of_remaining_installments))
                    # if there are full installments in overflow_amount

                    if number_of_overflows >= 1 and number_of_overflows < length_of_remaining_installments:
                        print('cheeeeeege')
                        i = 0
                        print(all_installment_id)

                        for each_overflow in range(0, number_of_overflows):
                            overflow_installment_id = all_installment_id[i]
                            installment = Installments.objects.get(
                                id=overflow_installment_id)
                            installment.remaining_amount = 0
                            installment.fully_paid = True
                            installment.save()

                            save_loan(loan, installment,
                                      new_earliest_installment_expected_amount)

                            loan.amount_paid += int(
                                new_earliest_installment_expected_amount)
                            loan.amount_remain -= int(
                                new_earliest_installment_expected_amount)
                            loan.save()

                            # del all_installment_id[i]

                            i += 1

                        final_earliest_installment_id = all_installment_id[i]

                        final_earliest_installment = Installments.objects.get(
                            id=final_earliest_installment_id)

                        if remaining_modulus > 0:
                            final_earliest_installment.remaining_amount -= remaining_modulus
                            final_earliest_installment.fully_paid = False
                            final_earliest_installment.save()

                            save_loan(loan, final_earliest_installment,
                                      remaining_modulus)
                            loan.amount_paid += int(remaining_modulus)
                            loan.amount_remain -= int(remaining_modulus)
                            loan.save()
                            messages.success(
                                request, 'Loan paid successfully')
                            return redirect('Loanapp:index')
                        else:
                            messages.success(
                                request, 'Loan paid successfully')
                            return redirect('Loanapp:index')

                    elif number_of_overflows >= 1 and number_of_overflows == length_of_remaining_installments:
                        i = 0
                        for each_overflow in range(0, number_of_overflows):
                            overflow_installment_id = all_installment_id[i]
                            print(overflow_installment_id)
                            installment = Installments.objects.get(
                                id=overflow_installment_id)
                            installment.remaining_amount = 0
                            installment.fully_paid = True
                            installment.save()

                            save_loan(loan, installment,
                                      new_earliest_installment_expected_amount)

                            loan.amount_paid += int(
                                new_earliest_installment_expected_amount)
                            loan.amount_remain -= int(
                                new_earliest_installment_expected_amount)
                            loan.save()
                            i += 1
                            print('next loop')

                        final_earliest_installment_id = min(all_installment_id)

                        final_earliest_installment = Installments.objects.get(
                            id=final_earliest_installment_id)

                        if remaining_modulus > 0:

                            LoanOverpayments.objects.create(
                                borrower=loan.borrower,
                                amount_paid=remaining_modulus,
                                date_of_payment=getcurrenttime()
                            )

                            messages.success(
                                request, 'Loan paid successfully')
                            return redirect('Loanapp:index')
                        else:
                            messages.success(
                                request, 'Loan paid successfully')
                            return redirect('Loanapp:index')

                    elif number_of_overflows == 1 and length_of_remaining_installments == 1:
                        print('we are in this block mami')
                        print(remaining_modulus)

                        _earliest_installment_id = min(all_installment_id)
                        _final_least_inst = Installments.objects.get(
                            id=_earliest_installment_id)
                        exp = _final_least_inst.expected_amount
                        # remaining_modulus

                        if int(remaining_modulus) == 0:
                            _final_least_inst.remaining_amount = 0
                            _final_least_inst.fully_paid = True
                            _final_least_inst.save()

                            save_loan(loan, _final_least_inst,
                                      exp)
                            loan.amount_paid += int(exp)
                            loan.amount_remain -= int(exp)
                            loan.save()

                            messages.success(
                                request, 'Loan paid successfully')
                            return redirect('Loanapp:index')

                        elif int(remaining_modulus) > 0:
                            _final_least_inst.remaining_amount = 0
                            _final_least_inst.fully_paid = True
                            _final_least_inst.save()

                            save_loan(loan, _final_least_inst,
                                      exp)
                            loan.amount_paid += int(exp)
                            loan.amount_remain -= int(exp)
                            loan.save()

                            LoanOverpayments.objects.create(
                                borrower=loan.borrower,
                                amount_paid=remaining_modulus,
                                date_of_payment=getcurrenttime()
                            )

                            messages.success(
                                request, 'Loan paid successfully')
                            return redirect('Loanapp:index')
                        elif int(remaining_modulus) < 0:
                            pass
                            messages.success(
                                request, 'Loan paid successfully')
                            return redirect('Loanapp:index')

                    elif number_of_overflows >= 1 and length_of_remaining_installments == 1:
                        final_least_inst_id = min(all_installment_id)
                        final_least_inst = Installments.objects.get(
                            id=final_least_inst_id)

                        if final_least_inst.remaining_amount == remaining_amount_after_removing_least_installment_amount:
                            final_least_inst.remaining_amount = 0
                            final_least_inst.fully_paid = True
                            final_least_inst.save()

                            save_loan(loan, final_least_inst,
                                      new_earliest_installment_expected_amount)

                            loan.amount_paid += int(
                                new_earliest_installment_expected_amount)
                            loan.amount_remain -= int(
                                new_earliest_installment_expected_amount)
                            loan.save()
                            messages.success(
                                request, 'Loan paid successfully')
                            return redirect('Loanapp:index')
                        elif final_least_inst.remaining_amount < remaining_amount_after_removing_least_installment_amount:
                            final_least_inst.remaining_amount -= remaining_amount_after_removing_least_installment_amount
                            final_least_inst.fully_paid = False
                            final_least_inst.save()

                            save_loan(loan, final_least_inst,
                                      remaining_amount_after_removing_least_installment_amount)
                            loan.amount_paid += int(
                                remaining_amount_after_removing_least_installment_amount)
                            loan.amount_remain -= int(
                                remaining_amount_after_removing_least_installment_amount)
                            loan.save()
                            messages.success(
                                request, 'Loan paid successfully')
                            return redirect('Loanapp:index')
                        elif final_least_inst.remaining_amount > remaining_amount_after_removing_least_installment_amount:
                            final_least_inst.remaining_amount = 0
                            final_least_inst.fully_paid = True
                            final_least_inst.save()

                            save_loan(loan, final_least_inst,
                                      new_earliest_installment_expected_amount)
                            loan.amount_paid += int(
                                new_earliest_installment_expected_amount)
                            loan.amount_remain -= int(
                                new_earliest_installment_expected_amount)
                            loan.save()
                            LoanOverpayments.objects.create(
                                borrower=loan.borrower,
                                amount_paid=excess_amount,
                                date_of_payment=getcurrenttime()
                            )
                            messages.success(
                                request, 'Loan paid successfully')
                            return redirect('Loanapp:index')
                    # there are no full installments in overflow amount
                    elif number_of_overflows == 0 and length_of_remaining_installments > 1:

                        _earliest_installment_id = min(all_installment_id)
                        _final_least_inst = Installments.objects.get(
                            id=_earliest_installment_id)
                        # remaining_modulus

                        _final_least_inst.remaining_amount -= remaining_modulus
                        _final_least_inst.fully_paid = False
                        _final_least_inst.save()

                        save_loan(loan, _final_least_inst,
                                  remaining_modulus)

                        loan.amount_paid += int(remaining_modulus)
                        loan.amount_remain -= int(remaining_modulus)
                        loan.save()

                        messages.success(
                            request, 'Loan paid successfully')
                        return redirect('Loanapp:index')

                    elif number_of_overflows >= 1 and number_of_overflows >= length_of_remaining_installments:
                        messages.success(request, 'pap ivo ndo imefail')
                        return redirect('Loanapp:index')
                    elif number_of_overflows == 0 and length_of_remaining_installments == 1:
                        _earliest_installment_id = min(all_installment_id)
                        _final_least_inst = Installments.objects.get(
                            id=_earliest_installment_id)
                        # remaining_modulus

                        _final_least_inst.remaining_amount -= remaining_modulus
                        _final_least_inst.fully_paid = False
                        _final_least_inst.save()

                        save_loan(loan, _final_least_inst,
                                  remaining_modulus)

                        loan.amount_paid += int(remaining_modulus)
                        loan.amount_remain -= int(remaining_modulus)
                        loan.save()

                        messages.success(
                            request, 'Loan paid successfully')
                        return redirect('Loanapp:index')

                elif int(amount) == least_installment_amount:
                    # no overflow
                    least_installment.remaining_amount = least_installment_amount - \
                        int(amount)
                    least_installment.fully_paid = True
                    least_installment.save()

                    save_loan(loan, least_installment, amount)

                    loan.amount_paid += int(amount)
                    loan.amount_remain -= int(amount)
                    loan.save()

                    messages.success(
                        request, 'Loan paid successfully')
                    return redirect('Loanapp:index')

                elif int(amount) < least_installment_amount:
                    # no overflow
                    least_installment.remaining_amount = least_installment_amount - \
                        int(amount)
                    least_installment.fully_paid = False
                    least_installment.save()

                    save_loan(loan, least_installment, amount)

                    # LoanRepayment.objects.create(
                    #     loan=loan,
                    #     tied_installment=least_installment,
                    #     amount_paid=amount,
                    #     date_of_payment=getcurrenttime()
                    # )

                    loan.amount_paid += int(amount)
                    loan.amount_remain -= int(amount)
                    loan.save()

                    messages.success(
                        request, 'Loan paid successfully')
                    return redirect('Loanapp:index')

            elif len(all_installment_id) == 1:
                only_installment_id = all_installment_id[0]
                only_installment = Installments.objects.get(
                    id=only_installment_id)
                only_installment_amount = only_installment.remaining_amount
                print(only_installment_amount)

                if int(amount) == only_installment_amount:
                    only_installment.remaining_amount = only_installment_amount - \
                        int(amount)
                    only_installment.fully_paid = True
                    only_installment.save()

                    save_loan(loan, only_installment, amount)

                    loan.amount_paid += int(amount)
                    loan.amount_remain -= int(amount)
                    loan.status = 'FULLY_PAID'
                    loan.fully_paid_on = getcurrenttime()
                    loan.save()

                    messages.success(
                        request, 'Loan paid successfully')
                    return redirect('Loanapp:index')

                elif int(amount) < only_installment_amount:
                    only_installment.remaining_amount = only_installment_amount - \
                        int(amount)
                    only_installment.fully_paid = False
                    only_installment.save()

                    save_loan(loan, only_installment, amount)

                    loan.amount_paid += int(amount)
                    loan.amount_remain -= int(amount)
                    loan.save()

                    messages.success(
                        request, 'Loan paid successfully')
                    return redirect('Loanapp:index')

                elif int(amount) > only_installment_amount:
                    excess_amount = int(amount) - int(only_installment_amount)
                    expected_amount = only_installment.expected_amount
                    only_installment.remaining_amount = 0
                    only_installment.fully_paid = True
                    only_installment.save()

                    save_loan(loan, only_installment, only_installment_amount)

                    loan.amount_paid += int(amount)
                    loan.amount_remain = 0
                    loan.status = 'FULLY_PAID'
                    loan.fully_paid_on = getcurrenttime()
                    loan.save()

                    LoanOverpayments.objects.create(
                        borrower=loan.borrower,
                        amount_paid=excess_amount,
                        date_of_payment=getcurrenttime()
                    )

                    messages.success(
                        request, 'Loan paid successfully')
                    return redirect('Loanapp:index')


# @login_required
# def loan_repay(request):
#     def save_loan(loan, only_installment, amount):
#         LoanRepayment.objects.create(
#             loan=loan,
#             tied_installment=only_installment,
#             amount_paid=amount,
#             date_of_payment=getcurrenttime()
#         )

#     if request.method == 'GET':
#         return render(request, 'Loanapp/loan_repay.html')
#     elif request.method == 'POST':
#         print(request.POST)
#         id_number = request.POST.get('id_number')
#         amount = request.POST.get('amount')

#         # get associated loan
#         all_active_loans = Loans.objects.filter(
#             status="DISBURSED")

#         print(all_active_loans)

#         associated_user_found = False

#         for each_loan in all_active_loans:
#             print(each_loan.borrower.national_id)
#             print(id_number)

#             if each_loan.borrower.national_id == id_number:
#                 associated_user_found = True
#             else:
#                 associated_user_found = False

#         if associated_user_found == False:
#             messages.warning(
#                 request, 'Sorry, No loan associated to this borrower found.')
#             return redirect('Loanapp:index')
#         else:
#             print('found record')
#             loan = Loans.objects.get(
#                 borrower__national_id=id_number, status="DISBURSED")

#             Transactions.objects.create(
#                 loan=loan,
#                 amount_paid=amount,
#                 date_of_payment=getcurrenttime()
#             )

#             # start evaluating installments and everything
#             all_related_installments = Installments.objects.filter(
#                 loan=loan, fully_paid=False).order_by('installment_number')

#             all_installment_id = []
#             for installment in all_related_installments:
#                 installment_id = installment.id
#                 all_installment_id.append(installment_id)

#             print(all_installment_id)

#             if len(all_installment_id) > 1:

#                 # get earliest installments
#                 earliest_installment = min(all_installment_id)
#                 least_installment = Installments.objects.get(
#                     id=earliest_installment)

#                 # get outstanding balance of least installment
#                 least_installment_amount = least_installment.remaining_amount
#                 print(least_installment_amount)

#                 if int(amount) > least_installment_amount:
#                     # overflow
#                     remaining_amount_after_removing_least_installment_amount = int(
#                         amount) - least_installment_amount

#                     least_installment.remaining_amount = 0
#                     least_installment.fully_paid = True
#                     least_installment.save()

#                     save_loan(loan, least_installment,
#                               least_installment_amount)

#                     loan.amount_paid += int(least_installment_amount)
#                     loan.amount_remain -= int(least_installment_amount)
#                     loan.save()

#                     all_installment_id.remove(earliest_installment)

#                     print(all_installment_id)

#                     # get least of the now all_installments

#                     new_earliest_installment_id = min(all_installment_id)

#                     # get instance of the same

#                     new_earliest_installment = Installments.objects.get(
#                         id=new_earliest_installment_id)

#                     # get expected amount of least installment
#                     new_earliest_installment_expected_amount = new_earliest_installment.expected_amount

#                     number_of_overflows = int(math.floor(
#                         remaining_amount_after_removing_least_installment_amount) / int(new_earliest_installment_expected_amount))

#                     remaining_modulus = int(remaining_amount_after_removing_least_installment_amount) % int(
#                         new_earliest_installment_expected_amount)

#                     print('remaining modulus ' + str(remaining_modulus))
#                     print('Number of overflows ' + str(number_of_overflows))

#                     length_of_remaining_installments = len(all_installment_id)

#                     print('number of remainign installments ' +
#                           str(length_of_remaining_installments))
#                     # if there are full installments in overflow_amount

#                     if number_of_overflows >= 1 and number_of_overflows < length_of_remaining_installments:
#                         i = 0
#                         for each_overflow in range(0, number_of_overflows):
#                             overflow_installment_id = all_installment_id[i]
#                             installment = Installments.objects.get(
#                                 id=overflow_installment_id)
#                             installment.remaining_amount = 0
#                             installment.fully_paid = True
#                             installment.save()

#                             save_loan(loan, installment,
#                                       new_earliest_installment_expected_amount)

#                             loan.amount_paid += int(
#                                 new_earliest_installment_expected_amount)
#                             loan.amount_remain -= int(
#                                 new_earliest_installment_expected_amount)
#                             loan.save()

#                             del all_installment_id[i]

#                             i += 1

#                         final_earliest_installment_id = min(all_installment_id)

#                         final_earliest_installment = Installments.objects.get(
#                             id=final_earliest_installment_id)

#                         if remaining_modulus > 0:
#                             final_earliest_installment.remaining_amount -= remaining_modulus
#                             final_earliest_installment.fully_paid = False
#                             final_earliest_installment.save()

#                             save_loan(loan, final_earliest_installment,
#                                       remaining_modulus)
#                             loan.amount_paid += int(remaining_modulus)
#                             loan.amount_remain -= int(remaining_modulus)
#                             loan.save()
#                             messages.success(
#                                 request, 'Loan paid successfully')
#                             return redirect('Loanapp:index')
#                         else:
#                             messages.success(
#                                 request, 'Loan paid successfully')
#                             return redirect('Loanapp:index')

#                     elif number_of_overflows >= 1 and number_of_overflows == length_of_remaining_installments:
#                         print('baaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaz')
#                         i = 0
#                         for each_overflow in range(0, number_of_overflows - 1):
#                             overflow_installment_id = all_installment_id[i]
#                             installment = Installments.objects.get(
#                                 id=overflow_installment_id)
#                             installment.remaining_amount = 0
#                             installment.fully_paid = True
#                             installment.save()

#                             save_loan(loan, installment,
#                                       new_earliest_installment_expected_amount)

#                             loan.amount_paid += int(
#                                 new_earliest_installment_expected_amount)
#                             loan.amount_remain -= int(
#                                 new_earliest_installment_expected_amount)
#                             loan.save()

#                             del all_installment_id[i]

#                             i += 1

#                         final_earliest_installment_id = min(all_installment_id)

#                         final_earliest_installment = Installments.objects.get(
#                             id=final_earliest_installment_id)

#                         if remaining_modulus > 0:
#                             final_earliest_installment.remaining_amount -= remaining_modulus
#                             final_earliest_installment.fully_paid = False
#                             final_earliest_installment.save()

#                             save_loan(loan, final_earliest_installment,
#                                       remaining_modulus)
#                             loan.amount_paid += int(remaining_modulus)
#                             loan.amount_remain -= int(remaining_modulus)
#                             loan.save()
#                             messages.success(
#                                 request, 'Loan paid successfully')
#                             return redirect('Loanapp:index')
#                         else:
#                             messages.success(
#                                 request, 'Loan paid successfully')
#                             return redirect('Loanapp:index')

#                     elif number_of_overflows == 1 and length_of_remaining_installments == 1:
#                         print('we are in this block mami')
#                         print(remaining_modulus)

#                         _earliest_installment_id = min(all_installment_id)
#                         _final_least_inst = Installments.objects.get(
#                             id=_earliest_installment_id)
#                         exp = _final_least_inst.expected_amount
#                         # remaining_modulus

#                         if int(remaining_modulus) == 0:
#                             _final_least_inst.remaining_amount = 0
#                             _final_least_inst.fully_paid = True
#                             _final_least_inst.save()

#                             save_loan(loan, _final_least_inst,
#                                       exp)
#                             loan.amount_paid += int(exp)
#                             loan.amount_remain -= int(exp)
#                             loan.save()

#                             messages.success(
#                                 request, 'Loan paid successfully')
#                             return redirect('Loanapp:index')

#                         elif int(remaining_modulus) > 0:
#                             _final_least_inst.remaining_amount = 0
#                             _final_least_inst.fully_paid = True
#                             _final_least_inst.save()

#                             save_loan(loan, _final_least_inst,
#                                       exp)
#                             loan.amount_paid += int(exp)
#                             loan.amount_remain -= int(exp)
#                             loan.save()

#                             LoanOverpayments.objects.create(
#                                 borrower=loan.borrower,
#                                 amount_paid=remaining_modulus,
#                                 date_of_payment=getcurrenttime()
#                             )

#                             messages.success(
#                                 request, 'Loan paid successfully')
#                             return redirect('Loanapp:index')
#                         elif int(remaining_modulus) < 0:
#                             pass
#                             messages.success(
#                                 request, 'Loan paid successfully')
#                             return redirect('Loanapp:index')

#                     elif number_of_overflows >= 1 and length_of_remaining_installments == 1:
#                         final_least_inst_id = min(all_installment_id)
#                         final_least_inst = Installments.objects.get(
#                             id=final_least_inst_id)

#                         if final_least_inst.remaining_amount == remaining_amount_after_removing_least_installment_amount:
#                             final_least_inst.remaining_amount = 0
#                             final_least_inst.fully_paid = True
#                             final_least_inst.save()

#                             save_loan(loan, final_least_inst,
#                                       new_earliest_installment_expected_amount)

#                             loan.amount_paid += int(
#                                 new_earliest_installment_expected_amount)
#                             loan.amount_remain -= int(
#                                 new_earliest_installment_expected_amount)
#                             loan.save()
#                             messages.success(
#                                 request, 'Loan paid successfully')
#                             return redirect('Loanapp:index')
#                         elif final_least_inst.remaining_amount < remaining_amount_after_removing_least_installment_amount:
#                             final_least_inst.remaining_amount -= remaining_amount_after_removing_least_installment_amount
#                             final_least_inst.fully_paid = False
#                             final_least_inst.save()

#                             save_loan(loan, final_least_inst,
#                                       remaining_amount_after_removing_least_installment_amount)
#                             loan.amount_paid += int(
#                                 remaining_amount_after_removing_least_installment_amount)
#                             loan.amount_remain -= int(
#                                 remaining_amount_after_removing_least_installment_amount)
#                             loan.save()
#                             messages.success(
#                                 request, 'Loan paid successfully')
#                             return redirect('Loanapp:index')
#                         elif final_least_inst.remaining_amount > remaining_amount_after_removing_least_installment_amount:
#                             final_least_inst.remaining_amount = 0
#                             final_least_inst.fully_paid = True
#                             final_least_inst.save()

#                             save_loan(loan, final_least_inst,
#                                       new_earliest_installment_expected_amount)
#                             loan.amount_paid += int(
#                                 new_earliest_installment_expected_amount)
#                             loan.amount_remain -= int(
#                                 new_earliest_installment_expected_amount)
#                             loan.save()
#                             LoanOverpayments.objects.create(
#                                 borrower=loan.borrower,
#                                 amount_paid=excess_amount,
#                                 date_of_payment=getcurrenttime()
#                             )
#                             messages.success(
#                                 request, 'Loan paid successfully')
#                             return redirect('Loanapp:index')
#                     # there are no full installments in overflow amount
#                     elif number_of_overflows == 0 and length_of_remaining_installments > 1:

#                         _earliest_installment_id = min(all_installment_id)
#                         _final_least_inst = Installments.objects.get(
#                             id=_earliest_installment_id)
#                         # remaining_modulus

#                         _final_least_inst.remaining_amount -= remaining_modulus
#                         _final_least_inst.fully_paid = False
#                         _final_least_inst.save()

#                         save_loan(loan, _final_least_inst,
#                                   remaining_modulus)

#                         loan.amount_paid += int(remaining_modulus)
#                         loan.amount_remain -= int(remaining_modulus)
#                         loan.save()

#                         messages.success(
#                             request, 'Loan paid successfully')
#                         return redirect('Loanapp:index')

#                     elif number_of_overflows >= 1 and number_of_overflows >= length_of_remaining_installments:
#                         messages.success(request, 'pap ivo ndo imefail')
#                         return redirect('Loanapp:index')
#                     elif number_of_overflows == 0 and length_of_remaining_installments == 1:
#                         _earliest_installment_id = min(all_installment_id)
#                         _final_least_inst = Installments.objects.get(
#                             id=_earliest_installment_id)
#                         # remaining_modulus

#                         _final_least_inst.remaining_amount -= remaining_modulus
#                         _final_least_inst.fully_paid = False
#                         _final_least_inst.save()

#                         save_loan(loan, _final_least_inst,
#                                   remaining_modulus)

#                         loan.amount_paid += int(remaining_modulus)
#                         loan.amount_remain -= int(remaining_modulus)
#                         loan.save()

#                         messages.success(
#                             request, 'Loan paid successfully')
#                         return redirect('Loanapp:index')

#                 elif int(amount) == least_installment_amount:
#                     # no overflow
#                     least_installment.remaining_amount = least_installment_amount - \
#                         int(amount)
#                     least_installment.fully_paid = True
#                     least_installment.save()

#                     save_loan(loan, least_installment, amount)

#                     loan.amount_paid += int(amount)
#                     loan.amount_remain -= int(amount)
#                     loan.save()

#                     messages.success(
#                         request, 'Loan paid successfully')
#                     return redirect('Loanapp:index')

#                 elif int(amount) < least_installment_amount:
#                     # no overflow
#                     least_installment.remaining_amount = least_installment_amount - \
#                         int(amount)
#                     least_installment.fully_paid = False
#                     least_installment.save()

#                     save_loan(loan, least_installment, amount)

#                     # LoanRepayment.objects.create(
#                     #     loan=loan,
#                     #     tied_installment=least_installment,
#                     #     amount_paid=amount,
#                     #     date_of_payment=getcurrenttime()
#                     # )

#                     loan.amount_paid += int(amount)
#                     loan.amount_remain -= int(amount)
#                     loan.save()

#                     messages.success(
#                         request, 'Loan paid successfully')
#                     return redirect('Loanapp:index')

#             elif len(all_installment_id) == 1:
#                 only_installment_id = all_installment_id[0]
#                 only_installment = Installments.objects.get(
#                     id=only_installment_id)
#                 only_installment_amount = only_installment.remaining_amount
#                 print(only_installment_amount)

#                 if int(amount) == only_installment_amount:
#                     only_installment.remaining_amount = only_installment_amount - \
#                         int(amount)
#                     only_installment.fully_paid = True
#                     only_installment.save()

#                     save_loan(loan, only_installment, amount)

#                     loan.amount_paid += int(amount)
#                     loan.amount_remain -= int(amount)
#                     loan.status = 'FULLY_PAID'
#                     loan.fully_paid_on = getcurrenttime()
#                     loan.save()

#                     messages.success(
#                         request, 'Loan paid successfully')
#                     return redirect('Loanapp:index')

#                 elif int(amount) < only_installment_amount:
#                     only_installment.remaining_amount = only_installment_amount - \
#                         int(amount)
#                     only_installment.fully_paid = False
#                     only_installment.save()

#                     save_loan(loan, only_installment, amount)

#                     loan.amount_paid += int(amount)
#                     loan.amount_remain -= int(amount)
#                     loan.save()

#                     messages.success(
#                         request, 'Loan paid successfully')
#                     return redirect('Loanapp:index')

#                 elif int(amount) > only_installment_amount:
#                     excess_amount = int(amount) - int(only_installment_amount)
#                     expected_amount = only_installment.expected_amount
#                     only_installment.remaining_amount = 0
#                     only_installment.fully_paid = True
#                     only_installment.save()

#                     save_loan(loan, only_installment, only_installment_amount)

#                     loan.amount_paid += int(amount)
#                     loan.amount_remain = 0
#                     loan.status = 'FULLY_PAID'
#                     loan.fully_paid_on = getcurrenttime()
#                     loan.save()

#                     LoanOverpayments.objects.create(
#                         borrower=loan.borrower,
#                         amount_paid=excess_amount,
#                         date_of_payment=getcurrenttime()
#                     )

#                     messages.success(
#                         request, 'Loan paid successfully')
#                     return redirect('Loanapp:index')


@login_required
def add_borrower_note(request, pk):
    if request.method == 'POST':
        borrower = Borrowers.objects.get(id=pk)
        user = request.user
        note = request.POST.get('note')

        BorrowerNotes.objects.create(
            borrower=borrower,
            notemadeby=user,
            note=note,
            note_date=getcurrenttime()
        )
        messages.success(request, 'Note created successfully.')
        return redirect('Loanapp:detail_borrower', pk=pk)


@login_required
def add_loan_note(request, pk):
    if request.method == 'POST':
        loan = Loans.objects.get(id=pk)
        user = request.user
        note = request.POST.get('note')

        LoanNotes.objects.create(
            loan=loan,
            notemadeby=user,
            note=note,
            note_date=getcurrenttime()
        )
        messages.success(request, 'Note created successfully.')
        return redirect('Loanapp:loan_detail', pk=pk)


@login_required
def delete_loan_note(request, pk, loan_id):
    my_loan_note = LoanNotes.objects.get(id=pk)
    my_loan_note.delete()
    messages.success(request, 'Note Deleted successfully.')
    return redirect('Loanapp:loan_detail', pk=loan_id)


# reports
@login_required
def active_borrowers(request):
    current_user_branch = request.user.userprofiles.branch

    if request.method == 'GET':

        if request.user.userprofiles.role == 'Admin':
            current_branch = request.session['current_branch']

            if current_branch == 'all':
                all_active_loans = Loans.objects.filter(
                    status="DISBURSED").order_by('-id')
            else:
                all_active_loans = Loans.objects.filter(
                    status="DISBURSED", borrower__branch__id=current_branch).order_by('-id')
            context = {
                'all_active_loans': all_active_loans
            }
            return render(request, 'Loanapp/active_borrowers.html', context)
        else:
            all_active_loans = Loans.objects.filter(
                status="DISBURSED", borrower__branch=current_user_branch).order_by('-id')
            context = {
                'all_active_loans': all_active_loans
            }
            return render(request, 'Loanapp/active_borrowers.html', context)

    elif request.method == 'POST':
        # get posted date:
        filter_date_ranger = request.POST.get('filterdate')
        filter_date_ranger = filter_date_ranger.replace(" ", "")
        mynew = filter_date_ranger.replace('-', ' ').split(' ')

        start_date = mynew[0]
        start_date = datetime.strptime(start_date, "%m/%d/%Y")
        start_date = datetime.strftime(start_date, "%Y-%m-%d")

        print(start_date)
        end_date = mynew[1]

        end_date = datetime.strptime(end_date, "%m/%d/%Y")
        end_date = datetime.strftime(end_date, "%Y-%m-%d")

        if request.user.userprofiles.role == 'Admin':
            current_branch = request.session['current_branch']

            if current_branch == 'all':
                all_active_loans = Loans.objects.filter(
                    status="DISBURSED", applied_at__range=[start_date, end_date])
            else:
                all_active_loans = Loans.objects.filter(
                    status="DISBURSED", applied_at__range=[start_date, end_date], borrower__branch__id=current_branch)

            print(all_active_loans)

            context = {
                'all_active_loans': all_active_loans
            }
            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/active_borrowers.html', context)
        else:
            all_active_loans = Loans.objects.filter(
                status="DISBURSED", applied_at__range=[start_date, end_date], borrower__branch=current_user_branch).order_by('-id')
            context = {
                'all_active_loans': all_active_loans
            }
            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/active_borrowers.html', context)


@login_required
def loans_due_today(request):
    current_user_branch = request.user.userprofiles.branch

    if request.method == 'GET':
        todays_date = getcurrenttime()
        if request.user.userprofiles.role == 'Admin':

            current_branch = request.session['current_branch']

            if current_branch == 'all':
                loans_due_today = Loans.objects.filter(
                    status="DISBURSED", endpayment_at=todays_date).order_by('-id')
            else:
                loans_due_today = Loans.objects.filter(
                    status="DISBURSED", endpayment_at=todays_date, borrower__branch__id=current_branch).order_by('-id')
            print(loans_due_today)
            context = {
                'loans_due_today': loans_due_today,
                'title': 'Loan Due Today',
            }
            return render(request, 'Loanapp/loans_due_today.html', context)
        else:
            loans_due_today = Loans.objects.filter(
                status="DISBURSED", borrower__branch=current_user_branch, endpayment_at=todays_date).order_by('-id')
            context = {
                'loans_due_today': loans_due_today,
                'title': 'Loan Due Today',
            }
            return render(request, 'Loanapp/loans_due_today.html', context)


@login_required
def loans_due_14_days(request):
    current_user_branch = request.user.userprofiles.branch

    if request.method == 'GET':
        todays_date = getcurrenttime()
        _14_days_from_today = todays_date + timedelta(days=14)
        if request.user.userprofiles.role == 'Admin':
            current_branch = request.session['current_branch']

            if current_branch == 'all':
                loans_due_today = Loans.objects.filter(
                    status="DISBURSED", endpayment_at__range=[todays_date, _14_days_from_today]).order_by('-id')
            else:
                loans_due_today = Loans.objects.filter(
                    status="DISBURSED", endpayment_at__range=[todays_date, _14_days_from_today], borrower__branch__id=current_branch).order_by('-id')
            print(loans_due_today)
            context = {
                'loans_due_today': loans_due_today,
                'title': 'Loan Due Next 14 days',
            }
            return render(request, 'Loanapp/loans_due_today.html', context)
        else:
            loans_due_today = Loans.objects.filter(
                status="DISBURSED", borrower__branch=current_user_branch, endpayment_at__range=[todays_date, _14_days_from_today]).order_by('-id')
            context = {
                'loans_due_today': loans_due_today,
                'title': 'Loan Due Next 14 days',
            }
            return render(request, 'Loanapp/loans_due_today.html', context)


@login_required
def installments_due_today(request):
    current_user_branch = request.user.userprofiles.branch

    if request.method == 'GET':
        if request.user.userprofiles.role == 'Admin':

            current_branch = request.session['current_branch']

            expected_date = getcurrenttime()
            if current_branch == 'all':
                all_installments = Installments.objects.filter(
                    loan__status="DISBURSED", expected_date=expected_date).order_by('-id')
            else:
                all_installments = Installments.objects.filter(
                    loan__status="DISBURSED", expected_date=expected_date, loan__borrower__branch__id=current_branch).order_by('-id')
            print(all_installments)
            context = {
                'all_installments': all_installments,
            }
            return render(request, 'Loanapp/installments_due_today.html', context)
        else:
            expected_date = getcurrenttime()
            all_installments = Installments.objects.filter(
                loan__status="DISBURSED", loan__borrower__branch=current_user_branch, expected_date=expected_date).order_by('-id')
            context = {
                'all_installments': all_installments,
            }
            return render(request, 'Loanapp/installments_due_today.html', context)


@login_required
def defaulted_installments(request):
    current_user_branch = request.user.userprofiles.branch

    if request.method == 'GET':
        if request.user.userprofiles.role == 'Admin':

            expected_date = getcurrenttime()
            current_branch = request.session['current_branch']

            if current_branch == 'all':
                all_installments = Installments.objects.filter(
                    fully_paid=False, expected_date__lt=expected_date).order_by('-id')
            else:
                all_installments = Installments.objects.filter(
                    fully_paid=False, expected_date__lt=expected_date, loan__borrower__branch__id=current_branch).order_by('-id')

            print(all_installments)
            context = {
                'all_installments': all_installments,
            }
            return render(request, 'Loanapp/defaulted_installments.html', context)
        else:
            expected_date = getcurrenttime()
            all_installments = Installments.objects.filter(
                fully_paid=False, expected_date__lt=expected_date, loan__borrower__branch=current_user_branch).order_by('-id')
            context = {
                'all_installments': all_installments,
            }
            return render(request, 'Loanapp/defaulted_installments.html', context)


@login_required
def defaulted_loans(request):
    current_user_branch = request.user.userprofiles.branch

    if request.method == 'GET':
        if request.user.userprofiles.role == 'Admin':

            expected_date = getcurrenttime()
            current_branch = request.session['current_branch']

            if current_branch == 'all':
                all_installments = Loans.objects.filter(
                    status="DISBURSED",
                    penalty__gt=0).order_by('-id')
            else:
                all_installments = Installments.objects.filter(
                    status="DISBURSED",
                    penalty__gt=0, borrower__branch__id=current_branch).order_by('-id')

            context = {
                'all_installments': all_installments,
            }

            return render(request, 'Loanapp/defaulted_loans.html', context)
        else:
            expected_date = getcurrenttime()
            all_installments = Installments.objects.filter(
                status="DISBURSED",
                penalty__gt=0, borrower__branch=current_user_branch).order_by('-id')
            context = {
                'all_installments': all_installments,
            }
            return render(request, 'Loanapp/defaulted_loans.html', context)


@login_required
def loan_repayments(request):
    current_user_branch = request.user.userprofiles.branch
    this_month = datetime.now().month
    if request.method == 'GET':

        if request.user.userprofiles.role == 'Admin':

            current_branch = request.session['current_branch']
            if current_branch == 'all':
                all_repayments = Transactions.objects.filter(
                    date_of_payment__month=this_month).order_by('-id')
            else:
                all_repayments = Transactions.objects.filter(
                    date_of_payment__month=this_month, loan__borrower__branch=current_branch).order_by('-id')

            total_amount = all_repayments.aggregate(Sum('amount_paid'))
            total_amount = total_amount['amount_paid__sum']
            context = {
                'all_repayments': all_repayments,
                'time_frame': 'This Month',
                'total_amount': total_amount,
            }
            return render(request, 'Loanapp/loan_repayments.html', context)
        else:
            all_repayments = Transactions.objects.filter(
                date_of_payment__month=this_month, loan__borrower__branch=current_user_branch).order_by('-id')
            total_amount = all_repayments.aggregate(Sum('amount_paid'))
            total_amount = total_amount['amount_paid__sum']
            context = {
                'all_repayments': all_repayments,
                'total_amount': total_amount,
                'time_frame': 'This Month',
            }
            return render(request, 'Loanapp/loan_repayments.html', context)

    elif request.method == 'POST':
        # get posted date:
        filter_date_ranger = request.POST.get('filterdate')
        filter_date_ranger = filter_date_ranger.replace(" ", "")
        mynew = filter_date_ranger.replace('-', ' ').split(' ')

        start_date = mynew[0]
        start_date = datetime.strptime(start_date, "%m/%d/%Y")
        start_date = datetime.strftime(start_date, "%Y-%m-%d")

        end_date = mynew[1]

        end_date = datetime.strptime(end_date, "%m/%d/%Y")
        end_date = datetime.strftime(end_date, "%Y-%m-%d")

        if request.user.userprofiles.role == 'Admin':
            current_branch = request.session['current_branch']
            if current_branch == 'all':
                all_repayments = Transactions.objects.filter(
                    date_of_payment__range=[start_date, end_date]).order_by('-id')
                time_frame = 'between ' + \
                    str(start_date) + ' and ' + str(end_date)
                total_amount = all_repayments.aggregate(Sum('amount_paid'))
                total_amount = total_amount['amount_paid__sum']
            else:
                all_repayments = Transactions.objects.filter(
                    date_of_payment__range=[start_date, end_date], loan__borrower__branch__id=current_branch).order_by('-id')
                time_frame = 'between ' + \
                    str(start_date) + ' and ' + str(end_date)
                total_amount = all_repayments.aggregate(Sum('amount_paid'))
                total_amount = total_amount['amount_paid__sum']

            context = {
                'all_repayments': all_repayments,
                'time_frame': time_frame,
                'total_amount': total_amount,
            }
            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/loan_repayments.html', context)
        else:
            all_repayments = Transactions.objects.filter(
                date_of_payment__range=[start_date, end_date], loan__borrower__branch=current_user_branch).order_by('-id')
            total_amount = all_repayments.aggregate(Sum('amount_paid'))
            time_frame = 'between ' + str(start_date) + ' and ' + str(end_date)
            total_amount = total_amount['amount_paid__sum']
            context = {
                'all_repayments': all_repayments,
                'time_frame': time_frame,
                'total_amount': total_amount,
            }
            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/loan_repayments.html', context)


@login_required
def loan_overpayments(request):
    current_user_branch = request.user.userprofiles.branch
    this_month = datetime.now().month
    if request.method == 'GET':

        if request.user.userprofiles.role == 'Admin':

            current_branch = request.session['current_branch']
            if current_branch == 'all':
                all_repayments = LoanOverpayments.objects.filter(
                    date_of_payment__month=this_month).order_by('-id')
            else:
                all_repayments = LoanOverpayments.objects.filter(
                    date_of_payment__month=this_month, borrower__branch=current_branch).order_by('-id')

            total_amount = all_repayments.aggregate(Sum('amount_paid'))
            total_amount = total_amount['amount_paid__sum']
            context = {
                'all_repayments': all_repayments,
                'time_frame': 'This Month',
                'total_amount': total_amount,
            }
            return render(request, 'Loanapp/loan_overpayments.html', context)
        else:
            all_repayments = LoanOverpayments.objects.filter(
                date_of_payment__month=this_month, borrower__branch=current_user_branch).order_by('-id')
            total_amount = all_repayments.aggregate(Sum('amount_paid'))
            total_amount = total_amount['amount_paid__sum']
            context = {
                'all_repayments': all_repayments,
                'total_amount': total_amount,
                'time_frame': 'This Month',
            }
            return render(request, 'Loanapp/loan_overpayments.html', context)

    elif request.method == 'POST':
        # get posted date:
        filter_date_ranger = request.POST.get('filterdate')
        filter_date_ranger = filter_date_ranger.replace(" ", "")
        mynew = filter_date_ranger.replace('-', ' ').split(' ')

        start_date = mynew[0]
        start_date = datetime.strptime(start_date, "%m/%d/%Y")
        start_date = datetime.strftime(start_date, "%Y-%m-%d")

        end_date = mynew[1]

        end_date = datetime.strptime(end_date, "%m/%d/%Y")
        end_date = datetime.strftime(end_date, "%Y-%m-%d")

        if request.user.userprofiles.role == 'Admin':
            current_branch = request.session['current_branch']
            if current_branch == 'all':
                all_repayments = LoanOverpayments.objects.filter(
                    date_of_payment__range=[start_date, end_date]).order_by('-id')
                time_frame = 'between ' + \
                    str(start_date) + ' and ' + str(end_date)
                total_amount = all_repayments.aggregate(Sum('amount_paid'))
                total_amount = total_amount['amount_paid__sum']
            else:
                all_repayments = LoanOverpayments.objects.filter(
                    date_of_payment__range=[start_date, end_date], borrower__branch__id=current_branch).order_by('-id')
                time_frame = 'between ' + \
                    str(start_date) + ' and ' + str(end_date)
                total_amount = all_repayments.aggregate(Sum('amount_paid'))
                total_amount = total_amount['amount_paid__sum']

            context = {
                'all_repayments': all_repayments,
                'time_frame': time_frame,
                'total_amount': total_amount,
            }
            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/loan_overpayments.html', context)
        else:
            all_repayments = LoanOverpayments.objects.filter(
                date_of_payment__range=[start_date, end_date], borrower__branch=current_user_branch).order_by('-id')
            total_amount = all_repayments.aggregate(Sum('amount_paid'))
            time_frame = 'between ' + str(start_date) + ' and ' + str(end_date)
            total_amount = total_amount['amount_paid__sum']
            context = {
                'all_repayments': all_repayments,
                'time_frame': time_frame,
                'total_amount': total_amount,
            }
            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/loan_overpayments.html', context)


@login_required
def disbursment_report_subform(request):
    current_user_branch = request.user.userprofiles.branch
    this_month = datetime.now().month
    if request.method == 'GET':

        if request.user.userprofiles.role == 'Admin':
            current_branch = request.session['current_branch']

            if current_branch == 'all':
                all_disbursed_loans = Loans.objects.filter(
                    Q(status="DISBURSED", disbursed_at__month=this_month) | Q(status="FULLY_PAID", disbursed_at__month=this_month)).order_by('-id')
                total_amount = Loans.objects.filter(
                    Q(status="DISBURSED", disbursed_at__month=this_month) | Q(status="FULLY_PAID", disbursed_at__month=this_month)).aggregate(Sum('expected_amount'))
                total_amount = total_amount['expected_amount__sum']
            else:
                all_disbursed_loans = Loans.objects.filter(
                    Q(status="DISBURSED", disbursed_at__month=this_month, borrower__branch__id=current_branch) | Q(status="FULLY_PAID", disbursed_at__month=this_month, borrower__branch__id=current_branch)).order_by('-id')
                total_amount = Loans.objects.filter(
                    Q(status="DISBURSED", disbursed_at__month=this_month, borrower__branch__id=current_branch) | Q(status="FULLY_PAID", disbursed_at__month=this_month, borrower__branch__id=current_branch)).aggregate(Sum('expected_amount'))
                total_amount = total_amount['expected_amount__sum']

            context = {
                'all_disbursed_loans': all_disbursed_loans,
                'time_frame': 'This Month',
                'total_amount': total_amount,
            }
            return render(request, 'Loanapp/disbursment_report_subform.html', context)
        else:
            all_disbursed_loans = Loans.objects.filter(
                Q(status="DISBURSED", disbursed_at__month=this_month, borrower__branch=current_user_branch) | Q(
                    status="FULLY_PAID", disbursed_at__month=this_month, borrower__branch=current_user_branch)).order_by('-id')
            total_amount = Loans.objects.filter(
                Q(status="DISBURSED", disbursed_at__month=this_month, borrower__branch=current_user_branch) | Q(
                    status="FULLY_PAID", disbursed_at__month=this_month, borrower__branch=current_user_branch)).aggregate(Sum('expected_amount'))
            total_amount = total_amount['expected_amount__sum']
            context = {
                'all_disbursed_loans': all_disbursed_loans,
                'time_frame': 'This Month',
                'total_amount': total_amount,
            }
            return render(request, 'Loanapp/disbursment_report_subform.html', context)

    elif request.method == 'POST':
        # get posted date:
        filter_date_ranger = request.POST.get('filterdate')
        filter_date_ranger = filter_date_ranger.replace(" ", "")
        mynew = filter_date_ranger.replace('-', ' ').split(' ')

        start_date = mynew[0]
        start_date = datetime.strptime(start_date, "%m/%d/%Y")
        start_date = datetime.strftime(start_date, "%Y-%m-%d")

        end_date = mynew[1]

        end_date = datetime.strptime(end_date, "%m/%d/%Y")
        end_date = datetime.strftime(end_date, "%Y-%m-%d")

        time_frame = 'between ' + str(start_date) + ' and ' + str(end_date)
        if request.user.userprofiles.role == 'Admin':
            current_branch = request.session['current_branch']

            if current_branch == 'all':
                all_disbursed_loans = Loans.objects.filter(
                    Q(status="DISBURSED", disbursed_at__range=[start_date, end_date]) | Q(status="FULLY_PAID", disbursed_at__range=[start_date, end_date])).order_by('-id')
                total_amount = Loans.objects.filter(
                    Q(status="DISBURSED", disbursed_at__range=[start_date, end_date]) | Q(status="FULLY_PAID", disbursed_at__range=[start_date, end_date])).aggregate(Sum('expected_amount'))
                total_amount = total_amount['expected_amount__sum']
            else:
                all_disbursed_loans = Loans.objects.filter(
                    Q(status="DISBURSED", disbursed_at__range=[start_date, end_date], borrower__branch__id=current_branch) | Q(status="FULLY_PAID", disbursed_at__range=[start_date, end_date], borrower__branch__id=current_branch)).order_by('-id')
                total_amount = Loans.objects.filter(
                    Q(status="DISBURSED", disbursed_at__range=[start_date, end_date], borrower__branch__id=current_branch) | Q(status="FULLY_PAID", disbursed_at__range=[start_date, end_date], borrower__branch__id=current_branch)).aggregate(Sum('expected_amount'))
                total_amount = total_amount['expected_amount__sum']

            context = {
                'all_disbursed_loans': all_disbursed_loans,
                'time_frame': time_frame,
                'total_amount': total_amount,
            }
            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/disbursment_report_subform.html', context)
        else:
            all_active_loans = Loans.objects.filter(
                Q(status="DISBURSED", disbursed_at__range=[start_date, end_date],  borrower__branch=current_user_branch) | Q(status="FULLY_PAID", disbursed_at__range=[start_date, end_date],  borrower__branch=current_user_branch)).order_by('-id')
            total_amount = Loans.objects.filter(
                Q(status="DISBURSED", disbursed_at__range=[start_date, end_date],  borrower__branch=current_user_branch) | Q(status="FULLY_PAID", disbursed_at__range=[start_date, end_date],  borrower__branch=current_user_branch)).aggregate(Sum('expected_amount'))
            total_amount = total_amount['expected_amount__sum']
            context = {
                'all_active_loans': all_active_loans,
                'time_frame': time_frame,
                'total_amount': total_amount,
            }
            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/disbursment_report_subform.html', context)


@login_required
def denied_loans(request):
    current_user_branch = request.user.userprofiles.branch

    if request.method == 'GET':

        if request.user.userprofiles.role == 'Admin':
            current_branch = request.session['current_branch']

            if current_branch == 'all':
                all_denied_loans = Loans.objects.filter(
                    status="DENIED").order_by('-id')
            else:
                all_denied_loans = Loans.objects.filter(
                    status="DENIED", borrower__branch__id=current_branch).order_by('-id')
            context = {
                'all_denied_loans': all_denied_loans
            }
            return render(request, 'Loanapp/denied_loans.html', context)
        else:
            all_denied_loans = Loans.objects.filter(
                status="DENIED", borrower__branch=current_user_branch).order_by('-id')
            context = {
                'all_denied_loans': all_denied_loans
            }
            return render(request, 'Loanapp/denied_loans.html', context)

    elif request.method == 'POST':
        # get posted date:
        filter_date_ranger = request.POST.get('filterdate')
        filter_date_ranger = filter_date_ranger.replace(" ", "")
        mynew = filter_date_ranger.replace('-', ' ').split(' ')

        start_date = mynew[0]
        start_date = datetime.strptime(start_date, "%m/%d/%Y")
        start_date = datetime.strftime(start_date, "%Y-%m-%d")

        end_date = mynew[1]

        end_date = datetime.strptime(end_date, "%m/%d/%Y")
        end_date = datetime.strftime(end_date, "%Y-%m-%d")

        if request.user.userprofiles.role == 'Admin':

            current_branch = request.session['current_branch']

            if current_branch == 'all':
                all_denied_loans = Loans.objects.filter(
                    status="DENIED", denied_at__range=[start_date, end_date])
            else:
                all_denied_loans = Loans.objects.filter(
                    status="DENIED", denied_at__range=[start_date, end_date], borrower__branch__id=current_branch)

            print(all_denied_loans)

            context = {
                'all_denied_loans': all_denied_loans
            }
            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/denied_loans.html', context)
        else:
            all_denied_loans = Loans.objects.filter(
                status="DENIED", denied_at__range=[start_date, end_date], borrower__branch=current_user_branch).order_by('-id')
            context = {
                'all_denied_loans': all_denied_loans
            }
            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/denied_loans.html', context)


@login_required
def new_borrowers(request):
    current_user_branch = request.user.userprofiles.branch

    if request.method == 'GET':

        start_date = getcurrenttime() - timedelta(days=7)
        end_date = getcurrenttime()
        if request.user.userprofiles.role == 'Admin':
            # registerd_on__range=[start_date, end_date]
            current_branch = request.session['current_branch']

            if current_branch == 'all':
                all_new_borrowers = Borrowers.objects.filter(
                    registerd_on__range=[start_date, end_date]).order_by('-id')
            else:
                all_new_borrowers = Borrowers.objects.filter(
                    registerd_on__range=[start_date, end_date], branch__id=current_branch).order_by('-id')
            context = {
                'all_new_borrowers': all_new_borrowers
            }
            return render(request, 'Loanapp/new_borrowers.html', context)
        else:
            all_new_borrowers = Borrowers.objects.filter(
                branch=current_user_branch, registerd_on__range=[start_date, end_date]).order_by('-id')
            context = {
                'all_new_borrowers': all_new_borrowers
            }
            return render(request, 'Loanapp/new_borrowers.html', context)

    elif request.method == 'POST':
        # get posted date:
        filter_date_ranger = request.POST.get('filterdate')
        filter_date_ranger = filter_date_ranger.replace(" ", "")
        mynew = filter_date_ranger.replace('-', ' ').split(' ')

        start_date = mynew[0]
        start_date = datetime.strptime(start_date, "%m/%d/%Y")
        start_date = datetime.strftime(start_date, "%Y-%m-%d")

        print(start_date)
        end_date = mynew[1]

        end_date = datetime.strptime(end_date, "%m/%d/%Y")
        end_date = datetime.strftime(end_date, "%Y-%m-%d")

        if request.user.userprofiles.role == 'Admin':
            current_branch = request.session['current_branch']

            if current_branch == 'all':
                all_new_borrowers = Borrowers.objects.filter(
                    registerd_on__range=[start_date, end_date])
            else:
                all_new_borrowers = Borrowers.objects.filter(
                    registerd_on__range=[start_date, end_date], branch__id=current_branch)

            context = {
                'all_new_borrowers': all_new_borrowers
            }
            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/new_borrowers.html', context)
        else:
            all_new_borrowers = Borrowers.objects.filter(
                registerd_on__range=[start_date, end_date], branch=current_user_branch).order_by('-id')
            context = {
                'all_new_borrowers': all_new_borrowers
            }
            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/new_borrowers.html', context)


@login_required
def registration_fee_summary(request):
    current_user_branch = request.user.userprofiles.branch

    if request.method == 'GET':

        if request.user.userprofiles.role == 'Admin':
            # registerd_on__range=[start_date, end_date]

            current_branch = request.session['current_branch']

            if current_branch == 'all':

                all_regestration_fees = MembershipFees.objects.all().order_by('-id')
            else:
                all_regestration_fees = MembershipFees.objects.filter(
                    borrower__branch__id=current_branch).order_by('-id')
            context = {
                'all_regestration_fees': all_regestration_fees
            }
            return render(request, 'Loanapp/registration_fee_summary.html', context)
        else:
            all_regestration_fees = MembershipFees.objects.filter(
                borrower__branch=current_user_branch).order_by('-id')
            context = {
                'all_regestration_fees': all_regestration_fees
            }
            return render(request, 'Loanapp/registration_fee_summary.html', context)

    elif request.method == 'POST':
        # get posted date:
        filter_date_ranger = request.POST.get('filterdate')
        filter_date_ranger = filter_date_ranger.replace(" ", "")
        mynew = filter_date_ranger.replace('-', ' ').split(' ')

        start_date = mynew[0]
        start_date = datetime.strptime(start_date, "%m/%d/%Y")
        start_date = datetime.strftime(start_date, "%Y-%m-%d")

        print(start_date)
        end_date = mynew[1]

        end_date = datetime.strptime(end_date, "%m/%d/%Y")
        end_date = datetime.strftime(end_date, "%Y-%m-%d")

        if request.user.userprofiles.role == 'Admin':
            current_branch = request.session['current_branch']

            if current_branch == 'all':
                all_regestration_fees = MembershipFees.objects.filter(
                    date_paid__range=[start_date, end_date]).order_by('-id')
            else:
                all_regestration_fees = MembershipFees.objects.filter(
                    date_paid__range=[start_date, end_date], borrower__branch__id=current_branch).order_by('-id')

            context = {
                'all_regestration_fees': all_regestration_fees
            }
            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/registration_fee_summary.html', context)
        else:
            all_regestration_fees = MembershipFees.objects.filter(
                date_paid__range=[start_date, end_date], borrower__branch=current_user_branch).order_by('-id')
            context = {
                'all_regestration_fees': all_regestration_fees
            }
            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/registration_fee_summary.html', context)


@login_required
def registration_fee_income(request):
    current_user_branch = request.user.userprofiles.branch

    if request.method == 'GET':

        if request.user.userprofiles.role == 'Admin':
            # registerd_on__range=[start_date, end_date]

            current_branch = request.session['current_branch']

            if current_branch == 'all':

                all_regestration_fees = MembershipFees.objects.all().count()
            else:
                all_regestration_fees = MembershipFees.objects.filter(
                    borrower__branch__id=current_branch).count()
            total_fee = all_regestration_fees * 500
            context = {
                'date': getcurrenttime(),
                'all_regestration_fees': all_regestration_fees,
                'total_fee': total_fee,
                'date_range': 'All'
            }
            return render(request, 'Loanapp/registration_fee_report.html', context)

    elif request.method == 'POST':
        # get posted date:
        filter_date_ranger = request.POST.get('filterdate')
        filter_date_ranger = filter_date_ranger.replace(" ", "")
        mynew = filter_date_ranger.replace('-', ' ').split(' ')

        start_date = mynew[0]
        start_date = datetime.strptime(start_date, "%m/%d/%Y")
        start_date = datetime.strftime(start_date, "%Y-%m-%d")

        print(start_date)
        end_date = mynew[1]

        end_date = datetime.strptime(end_date, "%m/%d/%Y")
        end_date = datetime.strftime(end_date, "%Y-%m-%d")

        if request.user.userprofiles.role == 'Admin':
            current_branch = request.session['current_branch']

            if current_branch == 'all':
                all_regestration_fees = MembershipFees.objects.filter(
                    date_paid__range=[start_date, end_date]).count()
            else:
                all_regestration_fees = MembershipFees.objects.filter(
                    date_paid__range=[start_date, end_date], borrower__branch__id=current_branch).count()

            total_fee = all_regestration_fees * 500
            context = {
                'date': getcurrenttime(),
                'all_regestration_fees': all_regestration_fees,
                'total_fee': total_fee,
                'date_range': 'All'
            }
            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/registration_fee_report.html', context)


@login_required
def profitability_report(request):
    current_user_branch = request.user.userprofiles.branch

    if request.method == 'GET':

        if request.user.userprofiles.role == 'Admin':
            # registerd_on__range=[start_date, end_date]

            this_month = datetime.now().month

            month_name = calendar.month_name[this_month]

            # Calculate profitability

            current_branch = request.session['current_branch']

            if current_branch == 'all':

                total_money_disbursed = Loans.objects.filter(
                    Q(status="DISBURSED", disbursed_at__month=this_month) | Q(status="FULLY_PAID", disbursed_at__month=this_month))

                if len(total_money_disbursed) >= 1:
                    total_money_disbursed = total_money_disbursed.aggregate(
                        Sum('expected_amount'))
                    total_money_disbursed = total_money_disbursed['expected_amount__sum']
                else:
                    total_money_disbursed = 0

                total_paid_loans = Transactions.objects.filter(
                    date_of_payment__month=this_month)

                if len(total_paid_loans) >= 1:
                    total_paid_loans = total_paid_loans.aggregate(
                        Sum('amount_paid'))
                    total_paid_loans = total_paid_loans['amount_paid__sum']
                else:
                    total_paid_loans = 0

                membership_fees = MembershipFees.objects.filter(
                    date_paid__month=this_month)

                print(membership_fees)

                if len(membership_fees) >= 1:
                    membership_fees = membership_fees.aggregate(Sum('amount'))

                    membership_fees = membership_fees['amount__sum']

                else:
                    membership_fees = 0

                # get all installments expected today.
            else:
                total_money_disbursed = Loans.objects.filter(
                    Q(status="DISBURSED", disbursed_at__month=this_month, borrower__branch__id=current_branch) | Q(status="FULLY_PAID", disbursed_at__month=this_month, borrower__branch__id=current_branch))

                if len(total_money_disbursed) >= 1:
                    total_money_disbursed = total_money_disbursed.aggregate(
                        Sum('expected_amount'))
                    total_money_disbursed = total_money_disbursed['expected_amount__sum']
                else:
                    total_money_disbursed = 0

                total_paid_loans = Transactions.objects.filter(
                    date_of_payment__month=this_month, loan__borrower__branch__id=current_branch)

                if len(total_paid_loans) >= 1:
                    total_paid_loans = total_paid_loans.aggregate(
                        Sum('amount_paid'))
                    total_paid_loans = total_paid_loans['amount_paid__sum']
                else:
                    total_paid_loans = 0

                membership_fees = MembershipFees.objects.filter(
                    date_paid__month=this_month, borrower__branch__id=current_branch)

                if len(membership_fees) >= 1:
                    membership_fees = membership_fees.aggregate(Sum('amount'))

                    membership_fees = membership_fees['amount__sum']
                else:
                    membership_fees = 0

            income = total_paid_loans + membership_fees
            grand_income = income - total_money_disbursed

            context = {
                'date': getcurrenttime(),
                'total_money_disbursed': total_money_disbursed,
                'total_paid_loans': total_paid_loans,
                'date_range': month_name,
                'membership_fees': membership_fees,
                'grand_income': grand_income,
                'when': 'This Month',
            }
            return render(request, 'Loanapp/profitability_report.html', context)

    elif request.method == 'POST':
        # get posted date:
        filter_date_ranger = request.POST.get('filterdate')
        filter_date_ranger = filter_date_ranger.replace(" ", "")
        mynew = filter_date_ranger.replace('-', ' ').split(' ')

        start_date = mynew[0]
        start_date = datetime.strptime(start_date, "%m/%d/%Y")
        start_date = datetime.strftime(start_date, "%Y-%m-%d")

        print(start_date)
        end_date = mynew[1]

        end_date = datetime.strptime(end_date, "%m/%d/%Y")
        end_date = datetime.strftime(end_date, "%Y-%m-%d")

        if request.user.userprofiles.role == 'Admin':
            current_branch = request.session['current_branch']

            if current_branch == 'all':

                total_money_disbursed = Loans.objects.filter(
                    Q(status="DISBURSED", disbursed_at__range=[start_date, end_date]) | Q(status="FULLY_PAID", disbursed_at__range=[start_date, end_date]))
                # hello = total_money_disbursed[0]

                if len(total_money_disbursed) >= 1:
                    total_money_disbursed = total_money_disbursed.aggregate(
                        Sum('expected_amount'))
                    total_money_disbursed = total_money_disbursed['expected_amount__sum']
                else:
                    total_money_disbursed = 0

                total_paid_loans = Transactions.objects.filter(
                    date_of_payment__range=[start_date, end_date])
                if len(total_paid_loans) >= 1:
                    total_paid_loans = total_paid_loans.aggregate(
                        Sum('amount_paid'))
                    total_paid_loans = total_paid_loans['amount_paid__sum']
                else:
                    total_paid_loans = 0

                membership_fees = MembershipFees.objects.filter(
                    date_paid__range=[start_date, end_date])

                if len(membership_fees) >= 1:
                    membership_fees = membership_fees.aggregate(Sum('amount'))
                    membership_fees = membership_fees['amount__sum']
                else:
                    membership_fees = 0

            else:
                total_money_disbursed = Loans.objects.filter(
                    Q(status="DISBURSED", disbursed_at__range=[start_date, end_date], borrower__branch__id=current_branch) | Q(status="FULLY_PAID", disbursed_at__range=[start_date, end_date], borrower__branch__id=current_branch))
                # hello = total_money_disbursed[0]

                if len(total_money_disbursed) >= 1:
                    total_money_disbursed = total_money_disbursed.aggregate(
                        Sum('expected_amount'))
                    total_money_disbursed = total_money_disbursed['expected_amount__sum']
                else:
                    total_money_disbursed = 0

                total_paid_loans = Transactions.objects.filter(
                    date_of_payment__range=[start_date, end_date], loan__borrower__branch__id=current_branch)
                if len(total_paid_loans) >= 1:
                    total_paid_loans = total_paid_loans.aggregate(
                        Sum('amount_paid'))
                    total_paid_loans = total_paid_loans['amount_paid__sum']
                else:
                    total_paid_loans = 0

                membership_fees = MembershipFees.objects.filter(
                    date_paid__range=[start_date, end_date], borrower__branch__id=current_branch)

                if len(membership_fees) >= 1:
                    membership_fees = membership_fees.aggregate(Sum('amount'))
                    membership_fees = membership_fees['amount__sum']
                else:
                    membership_fees = 0
            income = total_paid_loans + membership_fees
            grand_income = income - total_money_disbursed
            context = {
                'date': getcurrenttime(),
                'total_money_disbursed': total_money_disbursed,
                'total_paid_loans': total_paid_loans,
                'date_range': start_date + ' : : ' + end_date,
                'membership_fees': membership_fees,
                'grand_income': grand_income,
                'when': 'Between ' + start_date + ' and ' + end_date,
            }

            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/profitability_report.html', context)


# class GeneratePdf(View):
#     def get(self, request, *args, **kwargs):
#         if request.user.userprofiles.role == 'Admin':
#             # registerd_on__range=[start_date, end_date]

#             this_month = datetime.now().month

#             month_name = calendar.month_name[this_month]

#             # Calculate profitability

#             current_branch = request.session['current_branch']

#             if current_branch == 'all':

#                 total_money_disbursed = Loans.objects.filter(
#                     Q(status="DISBURSED", disbursed_at__month=this_month) | Q(status="FULLY_PAID", disbursed_at__month=this_month))

#                 if len(total_money_disbursed) >= 1:
#                     total_money_disbursed = total_money_disbursed.aggregate(
#                         Sum('expected_amount'))
#                     total_money_disbursed = total_money_disbursed['expected_amount__sum']
#                 else:
#                     total_money_disbursed = 0

#                 total_paid_loans = Transactions.objects.filter(
#                     date_of_payment__month=this_month)

#                 if len(total_paid_loans) >= 1:
#                     total_paid_loans = total_paid_loans.aggregate(
#                         Sum('amount_paid'))
#                     total_paid_loans = total_paid_loans['amount_paid__sum']
#                 else:
#                     total_paid_loans = 0

#                 membership_fees = MembershipFees.objects.filter(
#                     date_paid__month=this_month)

#                 print(membership_fees)

#                 if len(membership_fees) >= 1:
#                     membership_fees = membership_fees.aggregate(Sum('amount'))

#                     membership_fees = membership_fees['amount__sum']

#                 else:
#                     membership_fees = 0

#                     # get all installments expected today.
#             else:
#                 total_money_disbursed = Loans.objects.filter(
#                     Q(status="DISBURSED", disbursed_at__month=this_month, borrower__branch__id=current_branch) | Q(status="FULLY_PAID", disbursed_at__month=this_month, borrower__branch__id=current_branch))

#                 if len(total_money_disbursed) >= 1:
#                     total_money_disbursed = total_money_disbursed.aggregate(
#                         Sum('expected_amount'))
#                     total_money_disbursed = total_money_disbursed['expected_amount__sum']
#                 else:
#                     total_money_disbursed = 0

#                 total_paid_loans = Transactions.objects.filter(
#                     date_of_payment__month=this_month, loan__borrower__branch__id=current_branch)

#                 if len(total_paid_loans) >= 1:
#                     total_paid_loans = total_paid_loans.aggregate(
#                         Sum('amount_paid'))
#                     total_paid_loans = total_paid_loans['amount_paid__sum']
#                 else:
#                     total_paid_loans = 0

#                 membership_fees = MembershipFees.objects.filter(
#                     date_paid__month=this_month, borrower__branch__id=current_branch)

#                 if len(membership_fees) >= 1:
#                     membership_fees = membership_fees.aggregate(Sum('amount'))

#                     membership_fees = membership_fees['amount__sum']
#                 else:
#                     membership_fees = 0

#             income = total_paid_loans + membership_fees
#             grand_income = income - total_money_disbursed

#             context = {
#                 'date': getcurrenttime(),
#                 'total_money_disbursed': total_money_disbursed,
#                 'total_paid_loans': total_paid_loans,
#                 'date_range': month_name,
#                 'membership_fees': membership_fees,
#                 'grand_income': grand_income,
#                 'when': 'This Month',
#             }
#             open('temp.html',
#                  "w").write(render_to_string('Loanapp/profitability_report.html', context))

#             # Converting the HTML template into a PDF file
#             pdf = html_to_pdf('temp.html')

#             # rendering the template
#             return HttpResponse(pdf, content_type='application/pdf')

# def html_to_pdf_view(request):

#     if request.user.userprofiles.role == 'Admin':
#         # registerd_on__range=[start_date, end_date]

#         this_month = datetime.now().month

#         month_name = calendar.month_name[this_month]

#         # Calculate profitability

#         current_branch = request.session['current_branch']

#         if current_branch == 'all':

#             total_money_disbursed = Loans.objects.filter(
#                 Q(status="DISBURSED", disbursed_at__month=this_month) | Q(status="FULLY_PAID", disbursed_at__month=this_month))

#             if len(total_money_disbursed) >= 1:
#                 total_money_disbursed = total_money_disbursed.aggregate(
#                     Sum('expected_amount'))
#                 total_money_disbursed = total_money_disbursed['expected_amount__sum']
#             else:
#                 total_money_disbursed = 0

#             total_paid_loans = Transactions.objects.filter(
#                 date_of_payment__month=this_month)

#             if len(total_paid_loans) >= 1:
#                 total_paid_loans = total_paid_loans.aggregate(
#                     Sum('amount_paid'))
#                 total_paid_loans = total_paid_loans['amount_paid__sum']
#             else:
#                 total_paid_loans = 0

#             membership_fees = MembershipFees.objects.filter(
#                 date_paid__month=this_month)

#             print(membership_fees)

#             if len(membership_fees) >= 1:
#                 membership_fees = membership_fees.aggregate(Sum('amount'))

#                 membership_fees = membership_fees['amount__sum']

#             else:
#                 membership_fees = 0

#                 # get all installments expected today.
#         else:
#             total_money_disbursed = Loans.objects.filter(
#                 Q(status="DISBURSED", disbursed_at__month=this_month, borrower__branch__id=current_branch) | Q(status="FULLY_PAID", disbursed_at__month=this_month, borrower__branch__id=current_branch))

#             if len(total_money_disbursed) >= 1:
#                 total_money_disbursed = total_money_disbursed.aggregate(
#                     Sum('expected_amount'))
#                 total_money_disbursed = total_money_disbursed['expected_amount__sum']
#             else:
#                 total_money_disbursed = 0

#             total_paid_loans = Transactions.objects.filter(
#                 date_of_payment__month=this_month, loan__borrower__branch__id=current_branch)

#             if len(total_paid_loans) >= 1:
#                 total_paid_loans = total_paid_loans.aggregate(
#                     Sum('amount_paid'))
#                 total_paid_loans = total_paid_loans['amount_paid__sum']
#             else:
#                 total_paid_loans = 0

#             membership_fees = MembershipFees.objects.filter(
#                 date_paid__month=this_month, borrower__branch__id=current_branch)

#             if len(membership_fees) >= 1:
#                 membership_fees = membership_fees.aggregate(Sum('amount'))

#                 membership_fees = membership_fees['amount__sum']
#             else:
#                 membership_fees = 0

#             income = total_paid_loans + membership_fees
#             grand_income = income - total_money_disbursed

#             context = {
#                 'date': getcurrenttime(),
#                 'total_money_disbursed': total_money_disbursed,
#                 'total_paid_loans': total_paid_loans,
#                 'date_range': month_name,
#                 'membership_fees': membership_fees,
#                 'grand_income': grand_income,
#                 'when': 'This Month',
#             }

#             html_string = render_to_string(
#                 'Loanapp/profitability_report.html', context)

#             html = HTML(string=html_string)
#             html.write_pdf(target='/tmp/mypdf.pdf')

#             fs = FileSystemStorage('/tmp')
#             with fs.open('mypdf.pdf') as pdf:
#                 response = HttpResponse(pdf, content_type='application/pdf')
#                 response['Content-Disposition'] = 'attachment; filename="mypdf.pdf"'
#                 return response

#             return response


@login_required
def collection_rate(request):
    current_user_branch = request.user.userprofiles.branch

    if request.method == 'GET':

        if request.user.userprofiles.role == 'Admin':
            # registerd_on__range=[start_date, end_date]
            this_month = datetime.now().month

            month_name = calendar.month_name[this_month]

            # Calculate profitability
            current_branch = request.session['current_branch']

            if current_branch == 'all':
                installments_expected_this_month = Installments.objects.filter(
                    expected_date__month=this_month)

                if len(installments_expected_this_month) >= 1:
                    installments_expected_this_month = installments_expected_this_month.aggregate(
                        Sum('expected_amount'))
                    installments_expected_this_month = installments_expected_this_month[
                        'expected_amount__sum']
                else:
                    installments_expected_this_month = 1

                installments_paid_this_month = Transactions.objects.filter(
                    date_of_payment__month=this_month)

                if len(installments_paid_this_month) >= 1:

                    installments_paid_this_month = installments_paid_this_month.aggregate(
                        Sum('amount_paid'))
                    installments_paid_this_month = installments_paid_this_month['amount_paid__sum']
                else:
                    installments_paid_this_month = 1

                collection_rate = (installments_paid_this_month /
                                   installments_expected_this_month) * 100

                collection_rate = math.floor(collection_rate)

            else:
                installments_expected_this_month = Installments.objects.filter(
                    expected_date__month=this_month, loan__borrower__branch__id=current_branch)

                if len(installments_expected_this_month) >= 1:
                    installments_expected_this_month = installments_expected_this_month.aggregate(
                        Sum('expected_amount'))
                    installments_expected_this_month = installments_expected_this_month[
                        'expected_amount__sum']
                else:
                    installments_expected_this_month = 1

                installments_paid_this_month = Transactions.objects.filter(
                    date_of_payment__month=this_month, loan__borrower__branch__id=current_branch)

                if len(installments_paid_this_month) >= 1:

                    installments_paid_this_month = installments_paid_this_month.aggregate(
                        Sum('amount_paid'))
                    installments_paid_this_month = installments_paid_this_month['amount_paid__sum']
                else:
                    installments_paid_this_month = 1

                collection_rate = (installments_paid_this_month /
                                   installments_expected_this_month) * 100

                collection_rate = math.floor(collection_rate)
            context = {
                'date': getcurrenttime(),
                'installments_expected_this_month': installments_expected_this_month,
                'date_range': month_name,
                'installments_paid_this_month': installments_paid_this_month,
                'collection_rate': collection_rate,
                'when': 'This Month',
            }
            return render(request, 'Loanapp/collection_rate.html', context)

    elif request.method == 'POST':
        # get posted date:
        filter_date_ranger = request.POST.get('filterdate')
        filter_date_ranger = filter_date_ranger.replace(" ", "")
        mynew = filter_date_ranger.replace('-', ' ').split(' ')

        start_date = mynew[0]
        start_date = datetime.strptime(start_date, "%m/%d/%Y")
        start_date = datetime.strftime(start_date, "%Y-%m-%d")

        print(start_date)
        end_date = mynew[1]

        end_date = datetime.strptime(end_date, "%m/%d/%Y")
        end_date = datetime.strftime(end_date, "%Y-%m-%d")

        if request.user.userprofiles.role == 'Admin':

            current_branch = request.session['current_branch']

            if current_branch == 'all':

                installments_expected_this_month = Installments.objects.filter(
                    expected_date__range=[start_date, end_date])

                if len(installments_expected_this_month) >= 1:
                    installments_expected_this_month = installments_expected_this_month.aggregate(
                        Sum('expected_amount'))
                    installments_expected_this_month = installments_expected_this_month[
                        'expected_amount__sum']
                else:
                    installments_expected_this_month = 1

                installments_paid_this_month = Transactions.objects.filter(
                    date_of_payment__range=[start_date, end_date])

                if len(installments_paid_this_month) >= 1:

                    installments_paid_this_month = installments_paid_this_month.aggregate(
                        Sum('amount_paid'))
                    installments_paid_this_month = installments_paid_this_month['amount_paid__sum']
                else:
                    installments_paid_this_month = 0

                collection_rate = (installments_paid_this_month /
                                   installments_expected_this_month) * 100

            else:
                installments_expected_this_month = Installments.objects.filter(
                    expected_date__range=[start_date, end_date], loan__borrower__branch__id=current_branch)

                if len(installments_expected_this_month) >= 1:
                    installments_expected_this_month = installments_expected_this_month.aggregate(
                        Sum('expected_amount'))
                    installments_expected_this_month = installments_expected_this_month[
                        'expected_amount__sum']
                else:
                    installments_expected_this_month = 1

                installments_paid_this_month = Transactions.objects.filter(
                    date_of_payment__range=[start_date, end_date], loan__borrower__branch__id=current_branch)

                if len(installments_paid_this_month) >= 1:

                    installments_paid_this_month = installments_paid_this_month.aggregate(
                        Sum('amount_paid'))
                    installments_paid_this_month = installments_paid_this_month['amount_paid__sum']
                else:
                    installments_paid_this_month = 0

                collection_rate = (installments_paid_this_month /
                                   installments_expected_this_month) * 100

            context = {
                'date': getcurrenttime(),
                'installments_expected_this_month': installments_expected_this_month,
                'date_range': start_date + ' : : ' + end_date,
                'installments_paid_this_month': installments_paid_this_month,
                'collection_rate': collection_rate,
                'when': 'This Month',
            }
            messages.success(
                request, 'Date Filter applied and records updated successfully')
            return render(request, 'Loanapp/collection_rate.html', context)


# analysis
@login_required
def loans_applied_analysis(request):

    if request.user.userprofiles.role == 'Admin':

        current_branch = request.session['current_branch']

        if current_branch == 'all':

            new_loans_today = Loans.objects.filter(
                applied_at=getcurrenttime()).count()

            denied_loans_today = Loans.objects.filter(
                denied_at=getcurrenttime()).count()

            approved_loans_today = Loans.objects.filter(
                approved_at=getcurrenttime()).count()

            disbursed_loans_today = Loans.objects.filter(
                disbursed_at=getcurrenttime()).count()

            label2 = ['NEW', 'DENIED', 'APPROVED', 'DISBURSED']
            data2 = [new_loans_today, denied_loans_today,
                     approved_loans_today, disbursed_loans_today]

            # week
            one_week_before = getcurrenttime() - timedelta(days=7)
            new_loans_this_week = Loans.objects.filter(
                applied_at__range=[one_week_before, getcurrenttime()]).count()

            denied_loans_this_week = Loans.objects.filter(
                denied_at__range=[one_week_before, getcurrenttime()]).count()

            approved_loans_this_week = Loans.objects.filter(
                approved_at__range=[one_week_before, getcurrenttime()]).count()

            disbursed_loans_this_week = Loans.objects.filter(
                disbursed_at__range=[one_week_before, getcurrenttime()]).count()

            label4 = ['NEW', 'DENIED', 'APPROVED', 'DISBURSED']
            data4 = [new_loans_this_week, denied_loans_this_week,
                     approved_loans_this_week, disbursed_loans_this_week]

            # month
            current_month = getcurrenttime().month
            new_loans_this_month = Loans.objects.filter(
                applied_at__month=current_month).count()

            denied_loans_this_month = Loans.objects.filter(
                denied_at__month=current_month).count()

            approved_loans_this_month = Loans.objects.filter(
                approved_at__month=current_month).count()

            disbursed_loans_this_month = Loans.objects.filter(
                disbursed_at__month=current_month).count()

            label5 = ['NEW', 'DENIED', 'APPROVED', 'DISBURSED']
            data5 = [new_loans_this_month, denied_loans_this_month,
                     approved_loans_this_month, disbursed_loans_this_month]

            # SECOND ANALYSIS OF NUMBER OF LOANS

            county_model = Loans.objects.all().values_list("applied_at")

            county_count_rep = Counter([rep[0] for rep in county_model])
            county_amount_rep = {}

            for rep in county_count_rep:
                county_amount_rep[rep] = 0

            for month in county_model:
                for rep in county_amount_rep:
                    if month[0] == rep:
                        county_amount_rep[rep] += 1

            label3 = list(county_amount_rep.keys())
            data3 = list(county_amount_rep.values())

        else:
            new_loans_today = Loans.objects.filter(
                applied_at=getcurrenttime(), borrower__branch__id=current_branch).count()

            denied_loans_today = Loans.objects.filter(
                denied_at=getcurrenttime(), borrower__branch__id=current_branch).count()

            approved_loans_today = Loans.objects.filter(
                borrower__branch__id=current_branch, approved_at=getcurrenttime()).count()

            disbursed_loans_today = Loans.objects.filter(
                borrower__branch__id=current_branch, disbursed_at=getcurrenttime()).count()

            label2 = ['NEW', 'DENIED', 'APPROVED', 'DISBURSED']
            data2 = [new_loans_today, denied_loans_today,
                     approved_loans_today, disbursed_loans_today]

            # week
            one_week_before = getcurrenttime() - timedelta(days=7)
            new_loans_this_week = Loans.objects.filter(borrower__branch__id=current_branch,
                                                       applied_at__range=[one_week_before, getcurrenttime()]).count()

            denied_loans_this_week = Loans.objects.filter(borrower__branch__id=current_branch,
                                                          denied_at__range=[one_week_before, getcurrenttime()]).count()

            approved_loans_this_week = Loans.objects.filter(borrower__branch__id=current_branch,
                                                            approved_at__range=[one_week_before, getcurrenttime()]).count()

            disbursed_loans_this_week = Loans.objects.filter(borrower__branch__id=current_branch,
                                                             disbursed_at__range=[one_week_before, getcurrenttime()]).count()

            label4 = ['NEW', 'DENIED', 'APPROVED', 'DISBURSED']
            data4 = [new_loans_this_week, denied_loans_this_week,
                     approved_loans_this_week, disbursed_loans_this_week]

            # month
            current_month = getcurrenttime().month
            new_loans_this_month = Loans.objects.filter(borrower__branch__id=current_branch,
                                                        applied_at__month=current_month).count()

            denied_loans_this_month = Loans.objects.filter(borrower__branch__id=current_branch,
                                                           denied_at__month=current_month).count()

            approved_loans_this_month = Loans.objects.filter(borrower__branch__id=current_branch,
                                                             approved_at__month=current_month).count()

            disbursed_loans_this_month = Loans.objects.filter(borrower__branch__id=current_branch,
                                                              disbursed_at__month=current_month).count()

            label5 = ['NEW', 'DENIED', 'APPROVED', 'DISBURSED']
            data5 = [new_loans_this_month, denied_loans_this_month,
                     approved_loans_this_month, disbursed_loans_this_month]

            # SECOND ANALYSIS OF NUMBER OF LOANS

            county_model = Loans.objects.filter(
                borrower__branch__id=current_branch).values_list("applied_at")

            county_count_rep = Counter([rep[0] for rep in county_model])
            county_amount_rep = {}

            for rep in county_count_rep:
                county_amount_rep[rep] = 0

            for month in county_model:
                for rep in county_amount_rep:
                    if month[0] == rep:
                        county_amount_rep[rep] += 1

            label3 = list(county_amount_rep.keys())
            data3 = list(county_amount_rep.values())
        context = {
            'label3': label3,
            'data3': data3,
            'label2': label2,
            'data2': data2,
            'label4': label4,
            'data4': data4,
            'label5': label5,
            'data5': data5,
        }

        return render(request, 'Loanapp/analysis_dashboard.html', context)

    else:
        messages.warning(request, 'Invalid access')
        return redirect('Loanapp:index')


def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)

                if request.user.userprofiles.role == 'Admin':
                    request.session['current_branch'] = 'all'
                    print(request.session['current_branch'])

                messages.success(
                    request, 'Logged in Successfully as ' + request.user.username)
                return redirect('Loanapp:index')
            else:
                messages.warning(request, 'Account not activated')
                return render(request, 'Loanapp/login.html')
        else:
            messages.warning(request, 'Invalid Username or Password!')
            return render(request, 'Loanapp/login.html')
    return render(request, 'Loanapp/login.html')


def logout_user(request):
    logout(request)
    messages.success(request, 'Successfully Logged out.')
    return redirect('Loanapp:login_user')


def register_user(request):
    if request.method == 'GET':
        form = UserProfilesForm(request.POST or None)
        context = {
            'form': form,
        }
        return render(request, 'Loanapp/register_user.html', context)
    else:
        # profile data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        role = request.POST.get('role')
        branch = request.POST.get('branch')
        avatar = request.FILES['avatar']
        username = request.POST.get('email')

        try:
            username = username.lower()
            password = request.POST.get('password')
            user = User()
            user.username = username
            user.email = username
            user.is_active = True

            user.set_password(password)
            user.save()

            new_user_id = user.id
            new_user_instance = User.objects.get(id=new_user_id)
            branch_instace = Branch.objects.get(id=branch)
            UserProfiles.objects.create(
                user=new_user_instance,
                branch=branch_instace,
                role=role,
                first_name=first_name,
                last_name=last_name,
                email_address=username,
                phone_number=phone_number,
                avatar=avatar
            )

            messages.success(
                request, 'User Account created successfully.')
            return redirect('Loanapp:index')
        except:
            messages.warning(
                request, 'Error. Email already Taken. Please Try another Email.')
            return redirect('Loanapp:index')
