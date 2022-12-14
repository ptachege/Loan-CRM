from ast import mod
from pyexpat import model
from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField

Roles = (
    ('Admin', 'Admin'),
    ('Loan Officer', 'Loan Officer'),
    ('Loan Collection Officer', 'Loan Collection Officer'),
    ('Loan Verification Officer', 'Loan Verification Officer'),
)


class Branch(models.Model):

    branch_name = models.CharField(max_length=2000)
    branch_location = models.CharField(max_length=20000)
    address = models.CharField(max_length=20000)
    map_address = models.CharField(max_length=1000, blank=True, null=True)
    latitude = models.CharField(max_length=1000, blank=True, null=True)
    longitude = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:

        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'

    def __str__(self):
        return self.branch_name


class UserProfiles(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    role = models.CharField(max_length=100, choices=Roles)
    first_name = models.CharField(max_length=2000)
    last_name = models.CharField(max_length=2000)
    email_address = models.CharField(max_length=2000, blank=True, null=True)
    phone_number = models.CharField(max_length=2000, null=True, blank=True)
    avatar = CloudinaryField('image')

    class Meta:

        verbose_name = 'UserProfiles'
        verbose_name_plural = 'UserProfiles'

    def __str__(self):
        return self.first_name + ' ' + self.last_name


class Borrowers(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    # personal
    walaka_id = models.CharField(max_length=2000, blank=True, null=True)
    gen_num = models.IntegerField(blank=True, null=True)
    disbursment_number = models.CharField(max_length=20, blank=True, null=True)

    # walaka autogenerated id
    national_id = models.CharField(max_length=100)
    first_name = models.CharField(max_length=2000)
    last_name = models.CharField(max_length=2000)
    nickname = models.CharField(max_length=2000, null=True, blank=True)
    phone_number = models.CharField(max_length=2000, null=True, blank=True)
    alt_phone_number = models.CharField(max_length=2000, null=True, blank=True)
    gender = models.CharField(max_length=2000, null=True, blank=True)
    marital_status = models.CharField(max_length=2000, null=True, blank=True)
    next_of_kin_name = models.CharField(max_length=2000, null=True, blank=True)
    next_of_kin_id = models.CharField(max_length=2000, null=True, blank=True)
    next_of_kin_relationship = models.CharField(
        max_length=2000, null=True, blank=True)
    dob = models.DateField()

    # location
    address = models.CharField(max_length=2000)
    # map
    map_address = models.CharField(max_length=1000, blank=True, null=True)
    latitude = models.CharField(max_length=1000, blank=True, null=True)
    longitude = models.CharField(max_length=1000, blank=True, null=True)

    # dependants
    non_schooling = models.CharField(
        max_length=1000, default=0, blank=True, null=True)
    primary_dependants = models.CharField(
        max_length=1000, default=0, blank=True, null=True)
    secondary_dependants = models.CharField(
        max_length=1000, default=0, blank=True, null=True)
    tertiary_dependants = models.CharField(
        max_length=1000, default=0, blank=True, null=True)

    # paid membershipfee
    paid_membership_fee = models.BooleanField(default=False)

    # work related
    working_status = models.CharField(max_length=1000, blank=True, null=True)
    bussiness_address = models.CharField(
        max_length=1000, blank=True, null=True)
    bussiness_location = models.CharField(
        max_length=1000, blank=True, null=True)
    residence_town = models.CharField(max_length=1000, blank=True, null=True)
    estimate_building = models.CharField(
        max_length=1000, blank=True, null=True)
    street_house_number = models.CharField(
        max_length=1000, blank=True, null=True)
    inserted_at = models.DateField(auto_now_add=True)
    bussiness_age = models.CharField(max_length=1000, blank=True, null=True)
    bussiness_type = models.CharField(max_length=1000, blank=True, null=True)

    # loan security
    loan_security = models.CharField(max_length=1000, blank=True, null=True)

    # tied officers
    loan_officer = models.ForeignKey(
        UserProfiles, related_name='loan_officer', on_delete=models.CASCADE)
    loan_collection_officer = models.ForeignKey(
        UserProfiles, related_name='loan_collection_officer', on_delete=models.CASCADE)

    # bussiness Profitability
    good_day = models.IntegerField(blank=True, null=True)
    bad_day = models.IntegerField(blank=True, null=True)
    days_per_week = models.IntegerField(blank=True, null=True)
    stock_purchase = models.IntegerField(blank=True, null=True)
    transport = models.IntegerField(blank=True, null=True)
    rent = models.IntegerField(blank=True, null=True)
    salary = models.IntegerField(blank=True, null=True)
    other_expenses = models.IntegerField(blank=True, null=True)

    # images we have a seprate model for images.
    # id

    front_id_image = models.ImageField()
    back_id_image = models.ImageField()
    # Borrower Files
    files = models.FileField()

    # date
    registerd_on = models.DateField(auto_now_add=True, blank=True, null=True)

    class Meta:

        verbose_name = 'Borrowers'
        verbose_name_plural = 'Borrowers'

    def __str__(self):
        return self.first_name + ' ' + self.last_name


class Leads(models.Model):
    first_name = models.CharField(max_length=2000, blank=True, null=True)
    last_name = models.CharField(max_length=2000, blank=True, null=True)
    phone_number = models.CharField(max_length=2000, blank=True, null=True)
    location = models.CharField(max_length=2000, blank=True, null=True)
    bussiness_type = models.CharField(max_length=2000, blank=True, null=True)
    associated_officer = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:

        verbose_name = 'Leads'
        verbose_name_plural = 'Leads'

    def __str__(self):
        return self.first_name


class MembershipFees(models.Model):
    borrower = models.ForeignKey(Borrowers, on_delete=models.CASCADE)
    date_paid = models.DateField(auto_now_add=True)
    amount = models.FloatField(max_length=30000, default=500)

    class Meta:
        verbose_name = 'MembershipFees'
        verbose_name_plural = 'MembershipFeess'

    def __str__(self):
        return str(self.amount)


class Loans(models.Model):
    borrower = models.ForeignKey(Borrowers, on_delete=models.CASCADE)
    loan_type = models.CharField(max_length=1000, blank=True, null=True)
    expected_amount = models.FloatField(max_length=200000)
    loan_percentage = models.CharField(max_length=20000)
    period = models.CharField(max_length=20000)
    total_loan = models.FloatField(max_length=200000)
    payment_type = models.CharField(max_length=2000, blank=True, null=True)
    amount_paid = models.FloatField(max_length=10000, default=0)
    amount_remain = models.FloatField(max_length=10000, default=0)

    # purpose
    loan_purpose1 = models.CharField(max_length=20000, blank=True, null=True)
    loan_purpose2 = models.CharField(max_length=20000, blank=True, null=True)
    loan_purpose3 = models.CharField(max_length=20000, blank=True, null=True)
    loan_purpose4 = models.CharField(max_length=20000, blank=True, null=True)

    # status
    # NEW
    # APPROVED
    # DENIED
    # DISBURSED
    # FULLY_PAID
    status = models.CharField(max_length=200, default="NEW")

    # dates
    applied_at = models.DateField(blank=True, null=True)
    denied_at = models.DateField(blank=True, null=True)
    approved_at = models.DateField(blank=True, null=True)
    disbursed_at = models.DateField(blank=True, null=True)

    approved_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='approved_by', blank=True, null=True)
    denied_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='denied_by', blank=True, null=True)
    disbursed_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='disbursed_by', blank=True, null=True)

    startpayment_at = models.DateField(blank=True, null=True)
    endpayment_at = models.DateField(blank=True, null=True)
    fully_paid_on = models.DateField(blank=True, null=True)

    balance_today = models.FloatField(max_length=200000, blank=True, null=True)
    penalty = models.FloatField(default=0, max_length=2000)
    run_penalty_date = models.DateField(blank=True, null=True)

    class Meta:

        verbose_name = 'Loans'
        verbose_name_plural = 'Loans'

    def __str__(self):
        return self.loan_type


class Installments(models.Model):
    loan = models.ForeignKey(Loans, on_delete=models.CASCADE)
    installment_number = models.CharField(
        max_length=2000, blank=True, null=True)
    expected_amount = models.FloatField(max_length=10000, default=0)
    expected_date = models.DateField(blank=True, null=True)
    remaining_amount = models.FloatField(default=0)
    fully_paid = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.expected_amount = round(self.expected_amount, 2)
        self.remaining_amount = round(self.remaining_amount, 2)
        super(Installments, self).save(*args, **kwargs)

    class Meta:

        verbose_name = 'Installments'
        verbose_name_plural = 'Installments'

    def __str__(self):
        return str(self.installment_number)


class LoanRepayment(models.Model):
    loan = models.ForeignKey(Loans, on_delete=models.CASCADE)
    tied_installment = models.ForeignKey(
        Installments, on_delete=models.CASCADE)
    amount_paid = models.FloatField(blank=True, null=True)
    date_of_payment = models.DateField(blank=True, null=True)

    def __str__(self):
        return str(self.amount_paid)


class LoanOverpayments(models.Model):
    borrower = models.ForeignKey(Borrowers, on_delete=models.CASCADE)
    amount_paid = models.FloatField(blank=True, null=True)
    date_of_payment = models.DateField(blank=True, null=True)

    def __str__(self):
        return str(self.amount_paid)


class Transactions(models.Model):
    loan = models.ForeignKey(Loans, on_delete=models.CASCADE)
    amount_paid = models.FloatField(blank=True, null=True)
    date_of_payment = models.DateField(blank=True, null=True)

    def __str__(self):
        return str(self.amount_paid)


class LoanNotes(models.Model):
    loan = models.ForeignKey(Loans, on_delete=models.CASCADE)
    notemadeby = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.CharField(max_length=20000)
    note_date = models.DateField(auto_now_add=True)


class BorrowerNotes(models.Model):
    borrower = models.ForeignKey(Borrowers, on_delete=models.CASCADE)
    notemadeby = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.CharField(max_length=20000)
    note_date = models.DateField(auto_now_add=True)


class AvatarImages(models.Model):
    borrower = models.ForeignKey(Borrowers, on_delete=models.CASCADE)
    image = CloudinaryField('image')

    def __str__(self):
        return self.borrower.first_name


class Guarantors(models.Model):
    borrower = models.ForeignKey(Borrowers, on_delete=models.CASCADE)
    guarantors_full_name = models.CharField(
        max_length=20000, blank=True, null=True)
    guarantors_contact = models.CharField(
        max_length=20000, blank=True, null=True)
    guarantors_relation = models.CharField(
        max_length=20000, blank=True, null=True)

    class Meta:

        verbose_name = 'Guarantors'
        verbose_name_plural = 'Guarantors'

    def __str__(self):
        return self.guarantors_full_name


class Referees(models.Model):
    borrower = models.ForeignKey(Borrowers, on_delete=models.CASCADE)
    referee_full_name = models.CharField(
        max_length=2000, blank=True, null=True)
    referee_contact = models.CharField(
        max_length=20000, blank=True, null=True)
    referee_relation = models.CharField(
        max_length=20000, blank=True, null=True)

    class Meta:

        verbose_name = 'Referees'
        verbose_name_plural = 'Referees'

    def __str__(self):
        return self.referee_full_name


class Assets(models.Model):
    borrower = models.ForeignKey(Borrowers, on_delete=models.CASCADE)
    asset_full_name = models.CharField(
        max_length=2000, blank=True, null=True)
    value = models.CharField(
        max_length=2000, blank=True, null=True)
    description = models.CharField(
        max_length=2000, blank=True, null=True)

    class Meta:

        verbose_name = 'Assets'
        verbose_name_plural = 'Assets'

    def __str__(self):
        return self.asset_full_name


class Comments(models.Model):
    borrower = models.ForeignKey(Borrowers, on_delete=models.CASCADE)
    commented_by = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(
        max_length=20000, blank=True, null=True)
    commented_at = models.DateField(auto_now_add=True)

    class Meta:

        verbose_name = 'Comments'
        verbose_name_plural = 'Comments'

    def __str__(self):
        self.message
