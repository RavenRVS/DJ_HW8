import pytest
from django.conf import settings
from rest_framework.test import APIClient
from model_bakery import baker

from students.models import Student, Course


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def student_factory():
    def factory(*args, **kwargs):
        return baker.make(Student, *args, **kwargs)

    return factory


@pytest.fixture
def course_factory():
    def factory(*args, **kwargs):
        return baker.make(Course, *args, **kwargs)

    return factory


@pytest.fixture(autouse=True)
def use_new_settings(settings):
    settings.MAX_STUDENTS_PER_COURSE = 5


@pytest.mark.django_db
def test_receiving_one_course(client, student_factory, course_factory):
    courses = course_factory(_quantity=1, make_m2m=True)

    response = client.get(f'/api/v1/courses/{courses[0].id}/')

    assert response.status_code == 200
    data = response.json()
    assert data['name'] == courses[0].name


@pytest.mark.django_db
def test_receiving_list_course(client, student_factory, course_factory):
    courses = course_factory(_quantity=10, make_m2m=True)

    response = client.get('/api/v1/courses/')

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10
    for i, course in enumerate(data):
        assert course['name'] == courses[i].name


@pytest.mark.django_db
def test_course_filter_by_id(client, student_factory, course_factory):
    courses = course_factory(_quantity=10, make_m2m=True)
    course_id = courses[5].id

    response = client.get(f'/api/v1/courses/?id={course_id}')

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['id'] == course_id


@pytest.mark.django_db
def test_course_filter_by_name(client, student_factory, course_factory):
    courses = course_factory(_quantity=10, make_m2m=True)
    course_name = courses[5].name

    response = client.get(f'/api/v1/courses/?name={course_name}')

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['name'] == course_name


@pytest.mark.django_db
def test_create_course(client):
    count = Course.objects.count()
    student = Student.objects.create(name='Вадим')

    response = client.post('/api/v1/courses/', data={'name': 'My course', 'students': [str(student.id)]})

    assert response.status_code == 201
    assert Course.objects.count() == count + 1


@pytest.mark.django_db
def test_update_course(client, course_factory):
    courses = course_factory(_quantity=3, make_m2m=True)
    course_id = courses[1].id
    response = client.patch(f'/api/v1/courses/{course_id}/', data={'name': 'My course', 'students': []})

    assert response.status_code == 200
    data = response.json()
    assert data['id'] == course_id
    assert data['name'] == 'My course'


@pytest.mark.django_db
def test_delete_course(client, course_factory):
    courses = course_factory(_quantity=3, make_m2m=True)
    count = Course.objects.count()
    course_id = courses[1].id
    response = client.delete(f'/api/v1/courses/{course_id}/')

    assert response.status_code == 204
    assert Course.objects.count() == count - 1
    for course in Course.objects.all():
        assert course_id != course.id


@pytest.mark.parametrize('count_students, status_response, count_of_new_records',
                         [
                             ('4', '201', '1'),
                             ('6', '400', '0')
                         ])
@pytest.mark.django_db
def test_count_of_students_per_course(use_new_settings,
                                      client,
                                      student_factory,
                                      count_students,
                                      status_response,
                                      count_of_new_records):
    students = student_factory(_quantity=int(count_students))
    count = Course.objects.count()
    list_id_students = [str(student.id) for student in students]

    response = client.post('/api/v1/courses/', data={'name': 'My course', 'students': list_id_students})

    assert response.status_code == int(status_response)
    assert Course.objects.count() == count + int(count_of_new_records)
