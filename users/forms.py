from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

from users.models import UserProfile
from games.models import Game 

class UserRegistrationForm(UserCreationForm):
    """Форма регистрации пользователя"""
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=30, required=False, label="Имя")
    last_name = forms.CharField(max_length=30, required=False, label="Фамилия")
    
    gender = forms.ChoiceField(
        choices=UserProfile.GENDER_CHOICES, 
        required=False, 
        label="Пол",
        help_text="Не обязательно для заполнения"
    )
    age = forms.IntegerField(
        required=False, 
        min_value=0, 
        max_value=128, 
        label="Возраст",
        help_text="Не обязательно для заполнения"
    )
    education = forms.ChoiceField(
        choices=UserProfile.EDUCATION_CHOICES, 
        required=False, 
        label="Образование",
        help_text="Не обязательно для заполнения"
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'gender', 'age', 'education')
        labels = {
            'username': 'Имя пользователя',
            'password1': 'Пароль',
            'password2': 'Подтверждение пароля',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].required = True
        self.fields['email'].required = True
        self.fields['password1'].required = True
        self.fields['password2'].required = True
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'username',
            'email',
            Row(
                Column('password1', css_class='form-group col-md-6 mb-0'),
                Column('password2', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('gender', css_class='form-group col-md-4 mb-0'),
                Column('age', css_class='form-group col-md-4 mb-0'),
                Column('education', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Зарегистрироваться', css_class='btn btn-primary')
        )
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Сохраняем данные в профиль пользователя
            user.userprofile.gender = self.cleaned_data.get('gender', 'unknown')
            user.userprofile.age = self.cleaned_data.get('age')
            user.userprofile.education = self.cleaned_data.get('education', 'not_specified')
            user.userprofile.save()
        return user


class UserProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя"""
    
    class Meta:
        model = UserProfile
        fields = ['avatar', 'gender', 'age', 'education', 'is_public']
        labels = {
            'avatar': 'Аватар',
            'gender': 'Пол',
            'age': 'Возраст',
            'education': 'Образование',
            'is_public': 'Публичный профиль',
        }
        widgets = {
            'avatar': forms.FileInput(),
            'gender': forms.Select(),
            'age': forms.NumberInput(attrs={'min': '0', 'max': '128'}),
            'education': forms.Select(),
        }
    
    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age in (None, '', -1):
            return None
        try:
            age = int(age)
        except (ValueError, TypeError):
            return None
        if age < 0:
            return None
        if age > 128:
            raise forms.ValidationError("Возраст должен быть от 0 до 128 лет")
        return age
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['gender'].required = False
        self.fields['education'].required = False
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'avatar',
            'gender',
            'age',
            'education',
            'is_public',
            Submit('submit', 'Сохранить', css_class='btn btn-primary')
        )


class UserUpdateForm(forms.ModelForm):
    """Форма обновления основной информации пользователя"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'email',
            Submit('submit', 'Обновить', css_class='btn btn-primary')
        )

