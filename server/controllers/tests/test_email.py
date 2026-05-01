import pytest
from server.controllers.email import Email


def test_valid1():
    raw = 'abc@example.com'
    email = Email(raw)
    assert isinstance(email, Email)
    assert str(email) == raw

def test_valid2():
    raw = 'some-name@tandon.nyu.edu'
    email = Email(raw)
    assert isinstance(email, Email)
    assert str(email) == raw

def test_valid3():
    raw = 'a.b.c.d.e.f@mysite.gov'
    email = Email(raw)
    assert isinstance(email, Email)
    assert str(email) == raw

def test_valid4():
    raw = '123456@123456.com'
    email = Email(raw)
    assert isinstance(email, Email)
    assert str(email) == raw

def test_capitalized():
    raw = 'MY_USERNAME@DOMAIN.EDU'
    email = Email(raw)
    assert isinstance(email, Email)
    assert str(email) == raw

def test_mixed_case():
    raw = 'My_USErNaME@DoMAiN.eDU'
    email = Email(raw)
    assert isinstance(email, Email)
    assert str(email) == raw

def test_bad_type():
    with pytest.raises(TypeError):
        Email(42)

def test_empty():
    with pytest.raises(ValueError):
        Email('')

def test_missing_local():
    with pytest.raises(ValueError):
        Email('@abc.com')

def test_missing_domain():
    with pytest.raises(ValueError):
        Email('my_name@')

def test_missing_tld():
    with pytest.raises(ValueError):
        Email('abc@abc')

def test_too_short_tld():
    with pytest.raises(ValueError):
        Email('abc@abc.c')

def test_numbers_only_tld():
    with pytest.raises(ValueError):
        Email('abc@@abc.123')

def test_double_period():
    with pytest.raises(ValueError):
        Email('abc@abc..com')

def test_double_at_symbol():
    with pytest.raises(ValueError):
        Email('abc@@abc.com')

def test_leading_whitespace():
    with pytest.raises(ValueError):
        Email('   abc@example.com')

def test_trailing_whitespace():
    with pytest.raises(ValueError):
        Email('abc@example.com      ')
