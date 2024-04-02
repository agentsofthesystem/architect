import pytest
import random
import time

from flask import current_app
from selenium.webdriver.common.keys import Keys
from werkzeug.security import generate_password_hash

from application.config.config import DefaultConfig

# from application.models.user import UserSql

DOMAIN = "@REPLACE_APP_NAME.com"


@pytest.mark.usefixtures("selenium_local_driver")
class UserTest:
    pass


class Test_User_Signup(UserTest):
    # @classmethod
    # def teardown(cls):
    #    pass

    @pytest.mark.skip(reason="TODO: Fix this test")
    @pytest.mark.parametrize("url", ["http://localhost:5000/signup"])
    def test_user_bad_signup(self, url):
        config = DefaultConfig()

        form_user = '//*[@id="username"]'
        form_first = '//*[@id="firstname"]'
        form_last = '//*[@id="lastname"]'
        form_email = '//*[@id="email"]'
        form_pass = '//*[@id="password"]'
        form_submit = (
            "/html/body/div[3]/section/div/div[2]/div/div[1]/div/div[2]/form/div[5]/div/button"
        )

        banner = "/html/body/div[2]/div"

        self.driver.get(url)

        # generate random number 1-1000
        rand = random.randint(1, 10000)
        username = f"1nt3restingT3st{rand}"
        email = f"{username}{DOMAIN}"

        print(f"Email Used: {email}")

        # This part of the test will be a invalid password strength.
        self.driver.find_element_by_xpath(form_user).send_keys("TEST")
        self.driver.find_element_by_xpath(form_first).send_keys("TEST")
        self.driver.find_element_by_xpath(form_last).send_keys("TEST")
        self.driver.find_element_by_xpath(form_email).send_keys(email)
        self.driver.find_element_by_xpath(form_pass).send_keys("ABC")

        self.driver.find_element_by_xpath(form_submit).click()

        time.sleep(5)

        text = self.driver.find_element_by_xpath(banner).text

        assert "Password must be at least 7 characters." in text

    @pytest.mark.skip(reason="TODO: Fix this test")
    @pytest.mark.parametrize("url", ["http://localhost:5000/signup"])
    def test_user_good_signup(self, url):
        form_user = '//*[@id="username"]'
        form_first = '//*[@id="firstname"]'
        form_last = '//*[@id="lastname"]'
        form_email = '//*[@id="email"]'
        form_pass = '//*[@id="password"]'
        form_submit = (
            "/html/body/div[3]/section/div/div[2]/div/div[1]/div/div[2]/form/div[5]/div/button"
        )

        self.driver.get(url)

        # generate random number 1-1000
        rand = random.randint(1, 10000)
        username = f"1nt3restingT3st{rand}"
        email = f"{username}{DOMAIN}"

        # Now, update to a good password and try to read email.
        self.driver.find_element_by_xpath(form_user).send_keys("TEST")
        self.driver.find_element_by_xpath(form_first).send_keys("TEST")
        self.driver.find_element_by_xpath(form_last).send_keys("TEST")
        self.driver.find_element_by_xpath(form_email).send_keys(email)
        self.driver.find_element_by_xpath(form_pass).send_keys("ABC")
        self.driver.find_element_by_xpath(form_pass).send_keys("GOOD_PASSWORD")
        self.driver.find_element_by_xpath(form_submit).click()

        cur_url = self.driver.current_url  # 'http://localhost:5000/app/main'
        cur_url.split("/")

        print(cur_url)

        assert "app" in cur_url
        assert "main" in cur_url


class Test_User_Account(UserTest):
    # @classmethod
    # def teardown(cls):
    #    pass

    @pytest.mark.skip(reason="TODO: Fix this test")
    @pytest.mark.parametrize("url", ["http://localhost:5000/signin"])
    def test_user_account_page(self, url, client):
        config = DefaultConfig()

        self.driver.delete_all_cookies()

        signin_email = '//*[@id="email"]'
        signin_pass = '//*[@id="password"]'
        signign_remember = '//*[@id="check-remember"]'
        signin_submit = (
            "/html/body/div[3]/section/div/div[2]/div/div[1]/div/div[2]/form/div[4]/button"
        )

        self.driver.get(url)

        time.sleep(5)

        self.driver.find_element_by_xpath(signin_email).send_keys(config.DEFAULT_ADMIN_EMAIL)
        self.driver.find_element_by_xpath(signin_pass).send_keys(config.ADMIN_PASSWORD)
        self.driver.find_element_by_xpath(signign_remember).click()
        self.driver.find_element_by_xpath(signin_submit).click()

        time.sleep(5)

        account_url = "http://localhost:5000/app/account"
        self.driver.get(account_url)

        time.sleep(2)

        account_form_first = (
            "/html/body/main/div[2]/section[3]/div/div/div/div[2]/div[2]/form/div[1]/div/input"
        )
        account_form_submit = '//*[@id="account"]/div/div[2]/div[2]/form/div[6]/div/button'

        self.driver.find_element_by_xpath(account_form_first).clear()
        self.driver.find_element_by_xpath(account_form_first).send_keys("CHANGED")
        self.driver.find_element_by_xpath(account_form_submit).click()

        time.sleep(5)

        # obj = User.objects(email=config.DEFAULT_ADMIN_EMAIL)

        # assert obj[0].first_name == 'CHANGED'
