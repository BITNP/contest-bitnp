"""A Locust test script for simulating student users taking a quiz."""

# This locust test script example will simulate a user
# browsing the Locust documentation on https://docs.locust.io

import copy
import logging
import random
from urllib.parse import urlencode

from locust import HttpUser, between, task
from pyquery import PyQuery


class Question:
    """Represents a quiz question with multiple choice options.

    Args:
        id (str): The unique identifier for the question.
        options (list[str]): A list of possible answer options for the question.
    """

    def __init__(self, qid: str, options: list[str]) -> None:  # noqa: D107
        self.id = qid
        self.options = options

    def select(self) -> str:
        """Randomly selects an answer option."""
        return random.choice(self.options)  # noqa: S311


class StudentUser(HttpUser):
    """Represents a student user taking the quiz."""

    host = "http://localhost:8000"

    # we assume someone who is doing quiz,
    # generally has a quite short waiting time (between
    # 1 and 3 seconds), since the quiz is fast-paced
    wait_time = between(1, 3)
    questions: dict[str, Question] = {}
    answers: dict[str, str] = {}
    current_index = 0

    def on_start(self) -> None:
        """Start by waiting so that the simulated users won't all arrive at the same time."""
        self.wait()
        self._login()

    def _login(self) -> None:
        r = self.client.get("/contest/")
        logging.info(f"Login page response status: {r.status_code}")
        if r.url.find("/cas/login") != -1:
            logging.info("Redirected to login")
            self.login(r)

    def _get_quiz(self, content: bytes) -> None:
        pq = PyQuery(content)
        self.csrf: str = pq("form > input[type=hidden]").val()  # type:ignore  # noqa: PGH003
        print(self.csrf)
        inputs = pq("form fieldset label input")
        for input_elem in inputs:
            name = input_elem.attrib["name"]
            value = input_elem.attrib["value"]
            self.questions.setdefault(name, Question(qid=name, options=[])).options.append(
                value
            )
        self.questions_index = list(self.questions.keys())
        print(self.questions_index)

    def login(self, cas_response) -> None:  # noqa: ANN001, D102
        cookies = cas_response.cookies
        pq = PyQuery(cas_response.content)
        # 假设CAS登录表单有username和password字段，模拟登录
        form = pq(".form-horizontal")
        action: str = form.attr("action").split(";")[0]  # type: ignore  # noqa: PGH003
        if not action:
            return
        # 构造完整的CAS登录提交URL
        cas_post_url = f"http://localhost:28080{action}" if action.startswith("/") else action

        view_state_input = pq("#j_id1\\:javax\\.faces\\.ViewState\\:0")
        print(view_state_input)
        view_state = view_state_input.val()

        # 生成一个随机用户名字符串
        self.username = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=12))  # noqa: S311
        logging.info(f"Logging in as {self.username}")

        params = {
            "compose": "compose",
            "compose:username": self.username,
            "compose:password": self.username,
            "compose:j_idt30": "Login",
            "compose:j_idt32": "http://localhost:28080/cas/login?service=http%3A%2F%2Flocalhost%3A8000%2Faccounts%2Flogin%2F%3Fnext%3D%252Fcontest%252F",
            "javax.faces.ViewState": view_state,
        }
        data = urlencode(params)
        print(data, cookies.items())
        post_resp = self.client.post(
            cas_post_url,
            data=data,
            allow_redirects=True,
            cookies=cookies,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        print(post_resp.status_code, post_resp.url, post_resp.cookies.items())
        if post_resp.status_code == 200 and post_resp.url.find("/contest/") != -1:  # noqa: PLR2004
            return self._get_quiz(post_resp.content)

    def on_quiz_update(self) -> None:
        """Handle quiz update."""
        data = copy.deepcopy(self.answers)
        data["csrfmiddlewaretoken"] = self.csrf
        logging.info(f"User {self.username} submitting answers: {data}")
        self.client.post("/contest/update/", data=data)

    @task(5)
    def do_nothing(self) -> None:
        """Simulate students doing nothing."""
        pass

    @task(3)
    def do_new_quiz(self) -> None:
        """Simulate answering a new quiz question."""
        name = self.questions_index[self.current_index]
        self.current_index += 1
        if self.current_index >= len(self.questions_index):
            return
        self.answers[name] = self.questions[name].select()
        self.on_quiz_update()
