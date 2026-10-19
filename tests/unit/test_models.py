from docforja.models import CheckResult, CheckStatus, DoctorReport


def test_optional_error_does_not_make_report_unhealthy():
    report = DoctorReport(
        checks=[
            CheckResult(
                id="optional",
                label="Optional",
                status=CheckStatus.ERROR,
                summary="missing",
                required=False,
            )
        ]
    )

    assert report.healthy


def test_required_error_makes_report_unhealthy():
    report = DoctorReport(
        checks=[
            CheckResult(
                id="required",
                label="Required",
                status=CheckStatus.ERROR,
                summary="missing",
            )
        ]
    )

    assert not report.healthy
