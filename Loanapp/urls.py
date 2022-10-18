
from django.urls import path
from . import views

app_name = 'Loanapp'

urlpatterns = [
    path('', views.index, name='index'),
    #     path('html_to_pdf_view', views.html_to_pdf_view, name='html_to_pdf_view'),
    #     path('pdf/', views.GeneratePdf.as_view(), name='html_to_pdf_view'),
    path('switch_branch_to_all/', views.switch_branch_to_all,
         name='switch_branch_to_all'),
    path('switch_branch/<str:branch_id>/',
         views.switch_branch, name='switch_branch'),
    path("login_user/", views.login_user, name="login_user"),
    path("logout_user/", views.logout_user, name="logout_user"),
    path('register_branch/', views.register_branch, name='register_branch'),
    path('view_branches/', views.view_branches, name='view_branches'),
    path('register_user/', views.register_user, name='register_user'),
    path('list_officers/', views.list_officers, name='list_officers'),
    path('pared_officers/', views.pared_officers, name='pared_officers'),
    path('detail_officer/<int:pk>/', views.detail_officer, name='detail_officer'),

    # register borrowers
    path('register_borrower/', views.register_borrower, name='register_borrower'),
    path('register_lead/', views.register_lead, name='register_lead'),
    path('list_leads/', views.list_leads, name='list_leads'),
    path('list_borrowers/', views.list_borrowers, name='list_borrowers'),
    path('detail_borrower/<int:pk>/',
         views.detail_borrower, name='detail_borrower'),
    path('additional_info/<int:pk>/',
         views.additional_info, name='additional_info'),
    path('create_guarantor/<int:pk>/',
         views.create_guarantor, name='create_guarantor'),
    path('create_guarantor_ajax/<int:pk>/',
         views.create_guarantor_ajax, name='create_guarantor_ajax'),
    path('create_referee/<int:pk>/',
         views.create_referee, name='create_referee'),
    path('create_referee_ajax/<int:pk>/',
         views.create_referee_ajax, name='create_referee_ajax'),
    path('create_asset/<int:pk>/',
         views.create_asset, name='create_asset'),
    path('create_asset_ajax/<int:pk>/',
         views.create_asset_ajax, name='create_asset_ajax'),
    path('save_avatars/<int:pk>/',
         views.save_avatars, name='save_avatars'),


    # Loans
    path('apply_for_loan/', views.apply_for_loan, name='apply_for_loan'),
    path('perform_loan_validation/', views.perform_loan_validation,
         name='perform_loan_validation'),
    path('apply_loan_form/<int:pk>/', views.apply_loan_form,
         name='apply_loan_form'),
    path('approve_loan_list/', views.approve_loan_list, name='approve_loan_list'),

    path('approve_loan_details/<int:pk>/',
         views.approve_loan_details, name='approve_loan_details'),
    path('change_to_approved/<int:pk>/',
         views.change_to_approved, name='change_to_approved'),
    path('change_to_denied/<int:pk>/',
         views.change_to_denied, name='change_to_denied'),
    path('disburse_list/', views.disburse_list, name='disburse_list'),
    path('disburse_loan_details/<int:pk>/',
         views.disburse_loan_details, name='disburse_loan_details'),
    path('change_to_disbursed/<int:pk>/',
         views.change_to_disbursed, name='change_to_disbursed'),
    path('pay_membershipfee/<int:pk>/<int:loan_id>/',
         views.pay_membershipfee, name='pay_membershipfee'),
    path('loan_list/', views.loan_list, name='loan_list'),
    path('loan_overpayments/', views.loan_overpayments, name='loan_overpayments'),
    path('loan_history/', views.loan_history, name='loan_history'),
    path('loan_detail/<int:pk>/', views.loan_detail, name='loan_detail'),


    #     loan repayment starts here. Crazy and wild daaamn
    path('loan_repay/', views.loan_repay, name='loan_repay'),
    path('add_loan_note/<int:pk>/', views.add_loan_note, name='add_loan_note'),
    path('add_borrower_note/<int:pk>/',
         views.add_borrower_note, name='add_borrower_note'),
    path('delete_loan_note/<int:pk>/<int:loan_id>/',
         views.delete_loan_note, name='delete_loan_note'),

    # reports
    path('active_borrowers/', views.active_borrowers, name='active_borrowers'),
    path('new_borrowers/', views.new_borrowers, name='new_borrowers'),
    path('registration_fee_summary/', views.registration_fee_summary,
         name='registration_fee_summary'),
    path('registration_fee_income/', views.registration_fee_income,
         name='registration_fee_income'),
    path('profitability_report/', views.profitability_report,
         name='profitability_report'),
    path('collection_rate/', views.collection_rate,
         name='collection_rate'),
    path('denied_loans/', views.denied_loans, name='denied_loans'),
    path('loans_due_today/', views.loans_due_today, name='loans_due_today'),
    path('loans_due_14_days/', views.loans_due_14_days, name='loans_due_14_days'),
    path('installments_due_today/', views.installments_due_today,
         name='installments_due_today'),
    path('defaulted_installments/', views.defaulted_installments,
         name='defaulted_installments'),
    path('defaulted_loans/', views.defaulted_loans,
         name='defaulted_loans'),
    path('disbursment_report_subform/', views.disbursment_report_subform,
         name='disbursment_report_subform'),
    path('loan_repayments/', views.loan_repayments,
         name='loan_repayments'),


    #  Analysis
    path('loans_applied_analysis/', views.loans_applied_analysis,
         name='loans_applied_analysis'),

    # compute penalties
    path('compute_penalties/', views.compute_penalties, name='compute_penalties'),

]
