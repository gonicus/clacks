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
			<UUID><xsl:value-of select="/merge/properties/value[name='entry-uuid']/value/text()" /></UUID>
			<DN><xsl:value-of select="/merge/properties/value[name='dn']/value/text()" /></DN>
			<LastChanged><xsl:value-of select="/merge/properties/value[name='modify-date']/value/text()" /></LastChanged>
			<Extensions>
				<xsl:for-each select="/merge/defs/g:Objects/g:Object[g:Extends/g:Value=$class]">
					<Extension>
						<xsl:value-of select="g:Name" />
					</Extension>
				</xsl:for-each>
			</Extensions>
			<Extends>
				<xsl:for-each select="/merge/defs/g:Objects/g:Object[g:Name=$class]/g:Extends">
					<Extension>
						<xsl:value-of select="g:Value" />
					</Extension>
				</xsl:for-each>
			</Extends>
			<xsl:for-each select="/merge/defs/g:Objects/g:Object[g:Name=$class]/g:Attributes/g:Attribute">
				<xsl:if test="g:Indexed='true'">
					<xsl:variable name="propname">
						<xsl:value-of select="g:Name" />
					</xsl:variable>
					<Attribute>
						<Name><xsl:value-of select="g:Name" /></Name>
						<Type><xsl:value-of select="g:Type" /></Type>
						<xsl:for-each select="/merge/properties/value[name=$propname]">
							<Value><xsl:value-of select="value" /></Value>
						</xsl:for-each>
					</Attribute>
				</xsl:if>
			</xsl:for-each>
		</Object>
	</xsl:template>
</xsl:stylesheet>
