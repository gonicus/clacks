<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <xsl:output method="xml" indent="yes" encoding="UTF-8" />
    <xsl:template match="/">
    	<Object xmlns="http://www.gonicus.de/Objects" 
    		xmlns:g="http://www.gonicus.de/Objects">
    		<xsl:variable name="class">
    			<xsl:value-of select="/merge/class" />
    		</xsl:variable>
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

    			<!-- Skip attributes that do not have to be indexed-->
    			<!--<xsl:if test="g:Indexed='true'">-->
    				<xsl:variable name="propname">
    					<xsl:value-of select="g:Name" />
    				</xsl:variable>
    				<Attribute>
    					<Name><xsl:value-of select="g:Name" /></Name>
    					<Type><xsl:value-of select="g:Type" /></Type>

    					<xsl:if test="/merge/properties/property[name=$propname]/value">
                            <Values>
                                <xsl:for-each select="/merge/properties/property[name=$propname]">
                                    <Value><xsl:value-of select="value" /></Value>
                                </xsl:for-each>
                            </Values>

                            <!-- Create type dependend fields for basic types.
                                I guess this enables us to search for dates using
                                < > in the dbxml
                            -->
                            <xsl:if test="g:Type='Integer'">
                                <IntegerValues>
                                    <xsl:for-each select="/merge/properties/property[name=$propname]">
                                        <Value><xsl:value-of select="value" /></Value>
                                    </xsl:for-each>
                                </IntegerValues>
                            </xsl:if>
                            <xsl:if test="g:Type='Timestamp'">
                                <TimestampValues>
                                    <xsl:for-each select="/merge/properties/property[name=$propname]">
                                        <Value><xsl:value-of select="value" /></Value>
                                    </xsl:for-each>
                                </TimestampValues>
                            </xsl:if>
                            <xsl:if test="g:Type='Date'">
                                <DateValues>
                                    <xsl:for-each select="/merge/properties/property[name=$propname]">
                                        <Value><xsl:value-of select="value" /></Value>
                                    </xsl:for-each>
                                </DateValues>
                            </xsl:if>
    					</xsl:if>
    				</Attribute>
    			<!--</xsl:if>-->
    		</xsl:for-each>
    		</Attributes>
    	</Object>
    </xsl:template>
</xsl:stylesheet>
