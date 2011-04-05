<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:gosa="http://www.gonicus.de/Events">

	<xsl:output method="xml" indent="yes" encoding="UTF-8" />

	<xsl:template match="/">

		<schema targetNamespace="http://www.gonicus.de/Events"
			elementFormDefault="qualified" xmlns="http://www.w3.org/2001/XMLSchema">

			<!-- Include schema for each event -->
			<xsl:for-each select="/events/path">
				<include schemaLocation="{/events/@prefix}{text()}" />
			</xsl:for-each>

			<complexType name="Event">
				<choice maxOccurs="1" minOccurs="1">
					<group ref="gosa:Events"></group>
				</choice>
			</complexType>

			<group name="Events">
				<choice>

					<!-- Create the possible Events -->
					<xsl:for-each select="/events/path">
						<xsl:variable name="nodename">
							<xsl:value-of select="substring-before(text(), '.xsd')" />
						</xsl:variable>
						<element name="{$nodename}" type="gosa:{$nodename}"></element>
					</xsl:for-each>

				</choice>
			</group>

			<element name="Event" type="gosa:Event"></element>

		</schema>

	</xsl:template>
</xsl:stylesheet>
