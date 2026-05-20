from src.services.classifier import _extract_license_plate


def test_extracts_uppercase_state_prefixed_plate_from_spanish_email():
    body = (
        "Hola buen dia deseo cancelar la suscripcion de la 2012 Nissan Rogue "
        "Burgundy UT-791010 ya la vendi muchas gracias"
    )

    assert _extract_license_plate("Cancelar", body) == "791010"


def test_does_not_treat_spanish_article_plus_year_as_plate():
    body = "Hola buen dia deseo cancelar la suscripcion de la 2012 Nissan Rogue."

    assert _extract_license_plate("Cancelar", body) is None


def test_does_not_treat_email_date_year_as_plate():
    body = '---- on Tue, 19 May 2026 08:24:45 -0600 "Customer" wrote ----'

    assert _extract_license_plate("Quiero cancelar el parqueadero", body) is None


def test_does_not_treat_state_plus_zip_as_plate():
    body = "9855 Shadow Way Dallas TX 75243"

    assert _extract_license_plate("The View at Lake Highlands", body) is None


def test_context_keyword_still_extracts_alphanumeric_plate():
    body = "Plate carrier: MSC2683"

    assert _extract_license_plate("Add vehicle", body) == "MSC2683"


def test_state_prefix_still_extracts_numeric_parkm_plate_name():
    assert _extract_license_plate("CO-7705793", "") == "7705793"
