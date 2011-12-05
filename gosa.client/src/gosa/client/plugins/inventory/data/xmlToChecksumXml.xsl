<xsl:stylesheet version="1.0"
	xmlns:gosa="http://www.gonicus.de/Events" 
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:strip-space elements="*"/>
	<xsl:output method="xml" indent="yes" encoding="UTF-8" />

	<xsl:template match="@*|node()">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()" />
		</xsl:copy>
	</xsl:template>
	<xsl:template match="/gosa:Event/gosa:Inventory/gosa:DeviceID"></xsl:template>
	<xsl:template match="/gosa:Event/gosa:Inventory/gosa:HardwareUUID"></xsl:template>
	<xsl:template match="/gosa:Event/gosa:Inventory/gosa:AccessLog"></xsl:template>
	<xsl:template match="/gosa:Event/gosa:Inventory/gosa:USBDevice"></xsl:template>
	<xsl:template match="/gosa:Event/gosa:Inventory/gosa:Environment"></xsl:template>
	<xsl:template match="/gosa:Event/gosa:Inventory/gosa:Hardware/gosa:ReportGenerationTime"></xsl:template>
	<xsl:template match="/gosa:Event/gosa:Inventory/gosa:Hardware/gosa:ProcessorSpeed"></xsl:template>
	<xsl:template match="/gosa:Event/gosa:Inventory/gosa:Cpu/gosa:Speed"></xsl:template>
	<xsl:template match="/gosa:Event/gosa:Inventory/gosa:Hardware/gosa:Description"></xsl:template>
	<xsl:template match="/gosa:Event/gosa:Inventory/gosa:Drive/gosa:FreeSpace"></xsl:template>
</xsl:stylesheet>
