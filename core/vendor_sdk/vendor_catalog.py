"""Pre-registered vendor and product catalog for the Vendor Asset SDK."""

from __future__ import annotations

from vendor_sdk.vendor_models import ProductDefinition, VendorDefinition

VENDORS: tuple[VendorDefinition, ...] = (
    VendorDefinition("cisco", "Cisco", "CISCO", "Cisco collaboration and voice platforms"),
    VendorDefinition("microsoft", "Microsoft", "MICROSOFT", "Microsoft Teams and cloud telephony"),
    VendorDefinition("audiocodes", "AudioCodes", "AUDIOCODES", "AudioCodes SBC and management"),
    VendorDefinition("genesys", "Genesys", "GENESYS", "Genesys cloud contact center"),
    VendorDefinition("ribbon", "Ribbon", "RIBBON", "Ribbon session border controllers"),
    VendorDefinition("oracle", "Oracle", "ORACLE", "Oracle communications SBC"),
    VendorDefinition("avaya", "Avaya", "AVAYA", "Avaya enterprise communications"),
)

PRODUCTS: tuple[ProductDefinition, ...] = (
    # Cisco
    ProductDefinition("cisco-cube", "cisco", "CUBE", "CUBE", "SIP", "Cisco Session Border Controller"),
    ProductDefinition("cisco-cucm", "cisco", "CUCM", "CUCM", "COLLABORATION", "Cisco Unified CM"),
    ProductDefinition("cisco-unity", "cisco", "Unity Connection", "UNITY", "COLLABORATION", "Cisco Unity Connection"),
    ProductDefinition("cisco-expressway", "cisco", "Expressway", "EXPRESSWAY", "SIP", "Cisco Expressway"),
    ProductDefinition("cisco-cer", "cisco", "CER", "CER", "COLLABORATION", "Cisco Emergency Responder"),
    ProductDefinition("cisco-imp", "cisco", "IM&P", "IMP", "COLLABORATION", "Cisco IM and Presence"),
    ProductDefinition("cisco-uccx", "cisco", "UCCX", "UCCX", "COLLABORATION", "Cisco Unified Contact Center Express"),
    ProductDefinition("cisco-webex-calling", "cisco", "Webex Calling", "WEBEX-CALLING", "COLLABORATION", "Webex Calling"),
    # Microsoft
    ProductDefinition("microsoft-teams-phone", "microsoft", "Teams Phone", "TEAMS-PHONE", "COLLABORATION", "Microsoft Teams Phone"),
    ProductDefinition("microsoft-direct-routing", "microsoft", "Direct Routing", "DIRECT-ROUTING", "SIP", "Teams Direct Routing"),
    ProductDefinition("microsoft-operator-connect", "microsoft", "Operator Connect", "OPERATOR-CONNECT", "SIP", "Teams Operator Connect"),
    ProductDefinition("microsoft-calling-plans", "microsoft", "Calling Plans", "CALLING-PLANS", "COLLABORATION", "Microsoft Calling Plans"),
    ProductDefinition("microsoft-teams-rooms", "microsoft", "Teams Rooms", "TEAMS-ROOMS", "COLLABORATION", "Microsoft Teams Rooms"),
    # AudioCodes
    ProductDefinition("audiocodes-mediant", "audiocodes", "Mediant SBC", "MEDIANT", "SIP", "AudioCodes Mediant SBC"),
    ProductDefinition("audiocodes-ovoc", "audiocodes", "OVOC", "OVOC", "MONITORING", "AudioCodes OVOC"),
    # Genesys
    ProductDefinition("genesys-cloud", "genesys", "Genesys Cloud", "GENESYS-CLOUD", "COLLABORATION", "Genesys Cloud CX"),
    # Ribbon
    ProductDefinition("ribbon-sbc", "ribbon", "Ribbon SBC", "SBC", "SIP", "Ribbon session border controller"),
    # Oracle
    ProductDefinition("oracle-sbc", "oracle", "Oracle SBC", "SBC", "SIP", "Oracle communications SBC"),
)

VENDOR_BY_NAME: dict[str, VendorDefinition] = {vendor.name.lower(): vendor for vendor in VENDORS}
VENDOR_BY_SLUG: dict[str, VendorDefinition] = {vendor.slug.lower(): vendor for vendor in VENDORS}
VENDOR_BY_ID: dict[str, VendorDefinition] = {vendor.vendor_id: vendor for vendor in VENDORS}

PRODUCT_BY_NAME: dict[tuple[str, str], ProductDefinition] = {
    (vendor.name.lower(), product.name.lower()): product
    for vendor in VENDORS
    for product in PRODUCTS
    if product.vendor_id == vendor.vendor_id
}
PRODUCT_BY_SLUG: dict[tuple[str, str], ProductDefinition] = {
    (vendor.slug.lower(), product.slug.lower()): product
    for vendor in VENDORS
    for product in PRODUCTS
    if product.vendor_id == vendor.vendor_id
}
