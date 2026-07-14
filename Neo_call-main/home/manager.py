from django.contrib.auth.base_user import BaseUserManager



class UserManager(BaseUserManager):
    def create_user(self, name, age, gender, occupation, email, phone_number, password):
        if not phone_number:
            raise ValueError('Users must have an phone_number')
        if not email :
            raise ValueError('Users must have an email')
        if not name:
            raise ValueError("The Name field must be set")
        user = self.model(
            name=name,
            age=age,
            gender=gender, 
            occupation = occupation ,
            is_Verified = False,
            email=self.normalize_email(email),
            phone_number=phone_number,
            password = password
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, name, age, gender, occupation, email, phone_number, password=None):
        # Create and save a superuser with the given details.
        
        # Create a regular user first
        user = self.create_user(
            name=name,
            age=age,
            gender=gender,
            occupation=occupation,
            email=email,
            phone_number=phone_number,
            password=password
        )
        
        # Set additional superuser attributes
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        
        # Save the user with superuser privileges
        user.save(using=self._db)
        return user
    
    

    
    