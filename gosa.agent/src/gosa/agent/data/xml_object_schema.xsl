<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <xsl:output method="xml" indent="yes" encoding="UTF-8" />
    <xsl:template match="/">

        <xsd:schema 
            xmlns:g="http://www.gonicus.de/Objects" 
            targetNamespace="http://www.gonicus.de/Objects"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns="http://www.gonicus.de/Objects"
            elementFormDefault="qualified">

            <xsd:element name="Object" type="Object"></xsd:element>

            <xsd:complexType name="Object">
                <xsd:all>
                    <xsd:element type="xsd:string" name="UUID"
                        minOccurs="1" maxOccurs="1"></xsd:element>
                    <xsd:element type="xsd:string" name="Type"
                        minOccurs="1" maxOccurs="1"></xsd:element>
                    <xsd:element type="xsd:string" name="DN"
                        minOccurs="1" maxOccurs="1"></xsd:element>
                    <xsd:element type="xsd:string" name="LastChanged"
                        minOccurs="1" maxOccurs="1"></xsd:element>
                    <xsd:element type="Extensions" name="Extensions"
                        minOccurs="0" maxOccurs="1"></xsd:element>
                    <xsd:element type="Attributes" name="Attributes"
                        minOccurs="0" maxOccurs="1"></xsd:element>
                </xsd:all>
            </xsd:complexType>

            <xsd:complexType name="Extensions">
                <xsd:sequence>
                    <xsd:element type="xsd:string" name="Extension" 
                        minOccurs="1" maxOccurs="unbounded"></xsd:element>
                </xsd:sequence>
            </xsd:complexType>

            <xsd:complexType name="Attributes">
                <xsd:sequence>
                    <xsl:for-each select="/g:Objects/g:Object[g:Name='GenericUser']">
                        <xsl:variable name="object">
                            <xsl:value-of select="g:Name" />
                        </xsl:variable>
                        <xsl:for-each select="g:Attributes/g:Attribute">
                            <xsl:variable name="attr">
                                <xsl:value-of select="g:Name" />
                            </xsl:variable>
                            <xsl:variable name="type">
                                <xsl:choose>
                                    <xsl:when test="g:Type='String'">xsd:string</xsl:when>
                                    <xsl:when test="g:Type='Integer'">xsd:integer</xsl:when>
                                    <xsl:when test="g:Type='Boolean'">xsd:string</xsl:when>
                                    <xsl:when test="g:Type='Timestamp'">xsd:dateTime</xsl:when>
                                    <xsl:when test="g:Type='Date'">xsd:date</xsl:when>
                                    <xsl:otherwise>xsd:string</xsl:otherwise>
                                </xsl:choose>
                            </xsl:variable>
                            <xsl:element name="xsd:element">
                                <xsl:attribute name="type"><xsl:value-of select="$type" /></xsl:attribute>
                                <xsl:attribute name="xmlns">
                                    <xsl:value-of select="concat('http://www.gonicus.de/Objects/',$object)" />
                                </xsl:attribute>
                                <xsl:attribute name="name"><xsl:value-of select="g:Name" /></xsl:attribute>
                                <xsl:attribute name="minOccurs">0</xsl:attribute>
                                <xsl:attribute name="maxOccurs">unbounded</xsl:attribute>
                            </xsl:element>
                        </xsl:for-each>
                    </xsl:for-each>
                </xsd:sequence>
            </xsd:complexType>
        </xsd:schema>
    </xsl:template>
</xsl:stylesheet>
