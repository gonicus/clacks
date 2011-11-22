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

            <xsd:complexType name="Extensions">
                <xsd:sequence>
                    <xsd:element type="xsd:string" name="Extension" 
                        minOccurs="1" maxOccurs="unbounded"></xsd:element>
                </xsd:sequence>
            </xsd:complexType>

            <xsd:complexType name="StringAttribute">
                <xsd:sequence>
                    <xsd:element name="value" type="xsd:string" minOccurs="1" maxOccurs="unbounded"/>
                </xsd:sequence>
            </xsd:complexType>

            <xsd:complexType name="BooleanAttribute">
                <xsd:sequence>
                    <xsd:element name="value" type="xsd:string" minOccurs="1" maxOccurs="unbounded"/>
                </xsd:sequence>
            </xsd:complexType>

            <xsd:complexType name="DateTimeAttribute">
                <xsd:sequence>
                    <xsd:element name="value" type="xsd:string" minOccurs="1" maxOccurs="unbounded"/>
                </xsd:sequence>
            </xsd:complexType>

            <xsd:complexType name="DateAttribute">
                <xsd:sequence>
                    <xsd:element name="value" type="xsd:string" minOccurs="1" maxOccurs="unbounded"/>
                </xsd:sequence>
            </xsd:complexType>

            <xsd:complexType name="IntegerAttribute">
                <xsd:sequence>
                    <xsd:element name="value" type="xsd:string" minOccurs="1" maxOccurs="unbounded"/>
                </xsd:sequence>
            </xsd:complexType>

            <xsl:for-each select="/g:Objects/g:Object">
                <xsl:variable name="classname">
                    <xsl:value-of select="g:Name" />
                </xsl:variable>
    
                <xsd:element name="{$classname}" type="{$classname}" />

                <xsd:complexType name="{$classname}">
                    <xsd:all>
                        <xsd:element type="xsd:string" name="UUID" minOccurs="1" maxOccurs="1"></xsd:element>
                        <xsd:element type="xsd:string" name="Type" minOccurs="1" maxOccurs="1"></xsd:element>
                        <xsd:element type="xsd:string" name="DN" minOccurs="1" maxOccurs="1"></xsd:element>
                        <xsd:element type="xsd:string" name="LastChanged" minOccurs="1" maxOccurs="1"></xsd:element>
                        <xsd:element type="Extensions" name="Extensions" minOccurs="0" maxOccurs="1"></xsd:element>
                        <xsd:element name="Attributes" >
                            <xsd:complexType>
                                <xsd:sequence>
                                    <xsl:for-each select="g:Attributes/g:Attribute">
                                        <xsl:sort select="g:Name"/>
                                        <xsl:variable name="type">
                                            <xsl:choose>
                                                <xsl:when test="g:Type='String'">StringAttribute</xsl:when>
                                                <xsl:when test="g:Type='Integer'">IntegerAttribute</xsl:when>
                                                <xsl:when test="g:Type='Boolean'">BooleanAttribute</xsl:when>
                                                <xsl:when test="g:Type='Timestamp'">DateTimeAttribute</xsl:when>
                                                <xsl:when test="g:Type='Date'">DateAttribute</xsl:when>
                                                <xsl:otherwise>StringAttribute</xsl:otherwise>
                                            </xsl:choose>
                                        </xsl:variable>
                                        <xsl:variable name="attr">
                                            <xsl:value-of select="g:Name" />
                                        </xsl:variable>
                                        <xsl:element name="xsd:element">
                                            <xsl:attribute name="name"><xsl:value-of select="g:Name" /></xsl:attribute>
                                            <xsl:attribute name="type"><xsl:value-of select="$type" /></xsl:attribute>
                                            <xsl:attribute name="minOccurs">0</xsl:attribute>
                                            <xsl:attribute name="maxOccurs">1</xsl:attribute>
                                        </xsl:element>
                                    </xsl:for-each>
                                </xsd:sequence>
                            </xsd:complexType>
                        </xsd:element>
                    </xsd:all>
                </xsd:complexType>
            </xsl:for-each>
        </xsd:schema>
    </xsl:template>
</xsl:stylesheet>
