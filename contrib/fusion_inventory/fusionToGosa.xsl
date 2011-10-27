<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:gosa="http://www.gonicus.de/Events/FusionInventory">
	<xsl:output method="xml" indent="yes" encoding="UTF-8" />
	<xsl:template match="/">
		<Event xmlns="http://www.gonicus.de/Events">
			<xsl:for-each select="/REQUEST/CONTENT/BIOS">
			<Bios>
				<BiosDate><xsl:value-of select="BDATE" /></BiosDate>
                		<BiosManufacturer><xsl:value-of select="BMANUFACTURER" /></BiosManufacturer>
                		<BiosVersion><xsl:value-of select="BVERSION" /></BiosVersion>
                		<SystenManufacturer><xsl:value-of select="SMANUFACTURER" /></SystenManufacturer>
                		<SystemModel><xsl:value-of select="SMODEL" /></SystemModel>
                		<SystemSerial><xsl:value-of select="SSN" /></SystemSerial>
			</Bios>
			</xsl:for-each> 
			
			<xsl:for-each select="/REQUEST/CONTENT/SOFTWARES">
			<Software>
				<Publisher><xsl:value-of select="PUBLISHER" /></Publisher>
				<Type><xsl:value-of select="FROM" /></Type>
				<Name><xsl:value-of select="NAME" /></Name>
				<InstallDate><xsl:value-of select="INSTALLDATE" /></InstallDate>
				<Comments><xsl:value-of select="COMMENTS" /></Comments>
				<Version><xsl:value-of select="VERSION" /></Version>
				<Size><xsl:value-of select="FILESIZE" /></Size>
				<Folder><xsl:value-of select="FOLDER" /></Folder>
			</Software>
			</xsl:for-each> 
	

		</Event>
        </xsl:template>
</xsl:stylesheet>

