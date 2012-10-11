# -*- coding: utf-8 -*-

"""Tests common operations."""

from __future__ import unicode_literals

import signal
import time

import pytest

import psh
from psh import sh

import test
test.init(globals())


def test_command_arguments(test):
    """Tests command argument parsing."""

    process = sh.test()
    assert process.command() == [ "test" ]
    assert unicode(process) == "test"
    assert str(process) == unicode(process).encode("utf-8")

    process = sh("complex command name")("arg1", "arg2")
    assert process.command() == [ "complex command name", "arg1", "arg2" ]
    assert unicode(process) == "'complex command name' arg1 arg2"
    assert str(process) == unicode(process).encode("utf-8")

    process = sh.test(
        b"arg", b"space arg", b"carriage\rline", b"line\narg", b"tab\targ", br"slash\arg", b"quote'arg", b'quote"arg', b"тест", b"тест тест",
        "arg", "space arg", "carriage\rline", "line\narg", "tab\targ", r"slash\arg", "quote'arg", 'quote"arg', "тест", "тест тест",
        3, 2 ** 128, 2.0
    )
    assert process.command() == [ "test",
        b"arg", b"space arg", b"carriage\rline", b"line\narg", b"tab\targ", br"slash\arg", b"quote'arg", b'quote"arg', b"тест", b"тест тест",
        "arg", "space arg", "carriage\rline", "line\narg", "tab\targ", r"slash\arg", "quote'arg", 'quote"arg', "тест", "тест тест",
        "3", "340282366920938463463374607431768211456", "2.0"
    ]
    assert unicode(process) == ("test "
        r"""arg 'space arg' 'carriage\rline' 'line\narg' 'tab\targ' 'slash\\arg' "quote'arg" 'quote"arg' \xd1\x82\xd0\xb5\xd1\x81\xd1\x82 '\xd1\x82\xd0\xb5\xd1\x81\xd1\x82 \xd1\x82\xd0\xb5\xd1\x81\xd1\x82' """
        r"""arg 'space arg' 'carriage\rline' 'line\narg' 'tab\targ' 'slash\\arg' 'quote\'arg' 'quote"arg' тест 'тест тест' """
        "3 340282366920938463463374607431768211456 2.0"
    )
    assert str(process) == unicode(process).encode("utf-8")

    process = sh.test("space arg", s = "short_arg")
    assert process.command() == [ "test", "-s", "short_arg", "space arg" ]
    assert unicode(process) == "test -s short_arg 'space arg'"
    assert str(process) == unicode(process).encode("utf-8")

    process = sh.test("arg", long_long_arg = "long arg")
    assert process.command() == [ "test", "--long-long-arg", "long arg", "arg" ]
    assert unicode(process) == "test --long-long-arg 'long arg' arg"
    assert str(process) == unicode(process).encode("utf-8")

    process = sh.test("arg", none_arg = None)
    assert process.command() == [ "test", "--none-arg", "arg" ]
    assert unicode(process) == "test --none-arg arg"
    assert str(process) == unicode(process).encode("utf-8")


def test_invalid_command_arguments(test):
    """Tests invalid command arguments."""

    class Class:
        pass

    with pytest.raises(psh.InvalidArgument):
        sh.test(Class())

    with pytest.raises(psh.InvalidArgument):
        sh.test(_invalid = None)



def test_repeated_execution(test):
    """Tests repeated execution."""

    process = sh.true().execute()
    with pytest.raises(psh.InvalidOperation):
        process.execute()



def test_pid(test):
    """Tests pid()."""

    process = sh.sh("-c", "echo $$")

    with pytest.raises(psh.InvalidProcessState):
        process.pid()

    assert process.execute().stdout().strip() == unicode(process.pid())



def test_kill(test):
    """Tests kill()."""

    start_time = time.time()
    process = sh.sleep("3").execute(wait = False)
    process.kill()
    assert process.wait() == 143
    assert time.time() < start_time + 1



def test_wait(test):
    """Tests wait()."""

    start_time = time.time()
    process = sh.sleep("3").execute(wait = False)
    assert time.time() < start_time + 1
    assert process.wait() == 0
    assert time.time() >= start_time + 3


def test_wait_status(test):
    """Tests wait() return value."""

    assert sh.true().execute(wait = False).wait() == 0
    assert sh.true().execute(wait = False).wait(check_status = True) == 0

    assert sh.false().execute(wait = False).wait() == 1
    assert pytest.raises(psh.ExecutionError,
        lambda: sh.false().execute(wait = False).wait(check_status = True)).value.status() == 1


def test_wait_with_kill(test):
    """Tests wait(kill = ...)."""

    start_time = time.time()
    process = sh.sleep("3").execute(wait = False)
    assert process.wait(kill = signal.SIGTERM) == 143
    assert time.time() < start_time + 1


def test_invalid_wait(test):
    """Tests wait() on a pending process."""

    with pytest.raises(psh.InvalidProcessState):
        sh.true().wait()



def test_zero_exit_status(test):
    """Tests zero exit status."""

    assert sh.true().execute().status() == 0


def test_nonzero_exit_status(test):
    """Tests nonzero exit status."""

    assert pytest.raises(psh.ExecutionError,
        lambda: sh.false().execute()).value.status() == 1


def test_nonexisting_command(test):
    """Tests executing nonexistent."""

    assert pytest.raises(psh.ExecutionError,
        lambda: sh("nonexistent command")().execute()).value.status() == 127


def test_ok_statuses(test):
    """Tests _ok_statuses option."""

    assert sh.false(_ok_statuses = [ 0, 1 ] ).execute().status() == 1
    assert pytest.raises(psh.ExecutionError,
        lambda: sh.true(_ok_statuses = []).execute()).value.status() == 0
