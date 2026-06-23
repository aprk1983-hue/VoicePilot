"""AudioCodes SBC parser pack registration."""

from __future__ import annotations

from parser.parser_registry import ParserRegistry

from plugins.audiocodes.parser.sbc.show_certificates import AudioCodesShowCertificatesParser
from plugins.audiocodes.parser.sbc.show_configuration import AudioCodesShowConfigurationParser
from plugins.audiocodes.parser.sbc.show_ha_status import AudioCodesShowHaStatusParser
from plugins.audiocodes.parser.sbc.show_ip_group import AudioCodesShowIpGroupParser
from plugins.audiocodes.parser.sbc.show_licenses import AudioCodesShowLicensesParser
from plugins.audiocodes.parser.sbc.show_media_realm import AudioCodesShowMediaRealmParser
from plugins.audiocodes.parser.sbc.show_proxy_set import AudioCodesShowProxySetParser
from plugins.audiocodes.parser.sbc.show_routing_table import AudioCodesShowRoutingTableParser
from plugins.audiocodes.parser.sbc.show_sip_interface import AudioCodesShowSipInterfaceParser
from plugins.audiocodes.parser.sbc.show_sip_options import AudioCodesShowSipOptionsParser
from plugins.audiocodes.parser.sbc.show_tls_context import AudioCodesShowTlsContextParser
from plugins.audiocodes.parser.sbc.show_voip_status import AudioCodesShowVoipStatusParser


def register_audiocodes_sbc_parsers(registry: ParserRegistry) -> None:
    """Register all AudioCodes SBC CLI parsers."""
    registry.register(AudioCodesShowConfigurationParser())
    registry.register(AudioCodesShowVoipStatusParser())
    registry.register(AudioCodesShowSipInterfaceParser())
    registry.register(AudioCodesShowProxySetParser())
    registry.register(AudioCodesShowIpGroupParser())
    registry.register(AudioCodesShowRoutingTableParser())
    registry.register(AudioCodesShowTlsContextParser())
    registry.register(AudioCodesShowCertificatesParser())
    registry.register(AudioCodesShowMediaRealmParser())
    registry.register(AudioCodesShowLicensesParser())
    registry.register(AudioCodesShowHaStatusParser())
    registry.register(AudioCodesShowSipOptionsParser())
