<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

    <xsl:output method="xml" indent="yes" encoding="UTF-8" />
    <xsl:template match="/">
        <xsl:variable name="class">
            <xsl:value-of select="/merge/class" />
        </xsl:variable>

        <xsl:element name="{$class}" 
            xmlns:g="http://www.gonicus.de/Objects"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://www.gonicus.de/Objects objects.xsd"
            >
            <xsl:attribute name="xmlns">http://www.gonicus.de/Objects</xsl:attribute>
            <xsl:attribute namespace="http://www.w3.org/2001/XMLSchema-instance"
                name="schemaLocation">http://www.gonicus.de/Objects objects.xsd</xsl:attribute>
    		<Type><xsl:value-of select="$class" /></Type>
    		<UUID><xsl:value-of select="/merge/properties/property[name='entry-uuid']/value/text()" /></UUID>
    		<DN><xsl:value-of select="/merge/properties/property[name='dn']/value/text()" /></DN>
    		<LastChanged><xsl:value-of select="/merge/properties/property[name='modify-date']/value/text()" /></LastChanged>
    		<Extensions>
    			<xsl:for-each select="/merge/extensions">
    				<Extension>
    					<xsl:value-of select="extension" />
    				</Extension>
    			</xsl:for-each>
    		</Extensions>

    		<!--
    		<AvailableExtensions>
    			<xsl:for-each select="/merge/defs/g:Objects/g:Object[g:Extends/g:Value=$class]">
    				<Extension>
    					<xsl:value-of select="g:Name" />
    				</Extension>
    			</xsl:for-each>
    		</AvailableExtensions>
    		<CanExtend>
    			<xsl:for-each select="/merge/defs/g:Objects/g:Object[g:Name=$class]/g:Extends">
    				<Extension>
    					<xsl:value-of select="g:Value" />
    				</Extension>
    			</xsl:for-each>
    		</CanExtend>
    		-->

    		<Attributes>
    		<xsl:for-each select="/merge/defs/g:Objects/g:Object[g:Name=$class]/g:Attributes/g:Attribute">
                <xsl:sort select="g:Name"/>
    			<!-- Skip attributes that do not have to be indexed-->
    			<!--<xsl:if test="g:Indexed='true'">-->
                    <xsl:variable name="propname">
                        <xsl:value-of select="g:Name" />
                    </xsl:variable>
                    <xsl:if test="/merge/properties/property[name=$propname]/value">
                        <xsl:for-each select="/merge/properties/property[name=$propname]">
                            <xsl:element name="{$propname}"><xsl:value-of select="value" /></xsl:element>
                        </xsl:for-each>
                    </xsl:if>
    			<!--</xsl:if>-->
    		</xsl:for-each>
    		</Attributes>
        </xsl:element>
    </xsl:template>
</xsl:stylesheet>
