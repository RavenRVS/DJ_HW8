from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from django_testing.settings import MAX_STUDENTS_PER_COURSE
from students.models import Course


class CourseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course
        fields = ("id", "name", "students")

    def validate(self, data):
        action = self.context['request'].stream.method
        if action in ['POST', 'PATCH']:
            count_students = len(data['students'])
            if count_students <= MAX_STUDENTS_PER_COURSE:
                return data
            else:
                raise ValidationError(f'На один курс допустимо не более {MAX_STUDENTS_PER_COURSE} студентов')
