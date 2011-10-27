<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:gosa="http://www.gonicus.de/Events/FusionInventory">
	<xsl:output method="xml" indent="yes" encoding="UTF-8" />
	<xsl:template match="/">
		<Event xmlns="http://www.gonicus.de/Events">

			<ClientInformation>
				<DeviceID><xsl:value-of select="/REQUEST/DEVICEID" /></DeviceID>
				<QueryType><xsl:value-of select="/REQUEST/QUERY" /></QueryType>
				<ClientVersion><xsl:value-of select="/REQUEST/CONTENT/VERSIONCLIENT" /></ClientVersion>
			</ClientInformation>

			<xsl:for-each select="/REQUEST/CONTENT/STORAGES">
			<Storage>
				<Description><xsl:value-of select="DESCRIPTION" /></Description>
                		<DiskSize><xsl:value-of select="DISKSIZE" /></DiskSize>
                		<Firmware><xsl:value-of select="FIRMWARE" /></Firmware>
                		<Manufacturer><xsl:value-of select="MANUFACTURER" /></Manufacturer>
                		<Model><xsl:value-of select="MODEL" /></Model>
                		<Name><xsl:value-of select="NAME" /></Name>
                		<SCSI_CHID><xsl:value-of select="SCSI_CHID" /></SCSI_CHID>
                		<SCSI_COID><xsl:value-of select="SCSI_COID" /></SCSI_COID>
                		<SCSI_LUN><xsl:value-of select="SCSI_LUN" /></SCSI_LUN>
                		<SCSI_UNID><xsl:value-of select="SCSI_UNID" /></SCSI_UNID>
                		<Serial><xsl:value-of select="Serial" /></Serial>
                		<Type><xsl:value-of select="Type" /></Type>
			</Storage>
			</xsl:for-each> 

			<xsl:for-each select="/REQUEST/CONTENT/USERS">
			<Users>
				<Login><xsl:value-of select="LOGIN" /></Login>
			</Users>
			</xsl:for-each> 

			<xsl:for-each select="/REQUEST/CONTENT/ACCESSLOG">
			<AccessLog>
				<LoginDate><xsl:value-of select="LOGDATE" /></LoginDate>
                		<UserID><xsl:value-of select="USERID" /></UserID>
			</AccessLog>
			</xsl:for-each> 

			<xsl:for-each select="/REQUEST/CONTENT/SOUNDS">
			<SoundHardware>
				<Description><xsl:value-of select="DESCRIPTION" /></Description>
                		<Manufacturer><xsl:value-of select="MANUFACTURER" /></Manufacturer>
                		<Name><xsl:value-of select="Name" /></Name>
			</SoundHardware>
			</xsl:for-each> 

			<xsl:for-each select="/REQUEST/CONTENT/VIDEOS">
			<VideoHardware>
                		<Name><xsl:value-of select="Name" /></Name>
				<Memory><xsl:value-of select="MEMORY" /></Memory>
                		<Chipset><xsl:value-of select="CHIPSET" /></Chipset>
                		<Resolution><xsl:value-of select="RESOLUTION" /></Resolution>
			</VideoHardware>
			</xsl:for-each> 

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
				<Name><xsl:value-of select="NAME" /></Name>
				<Type><xsl:value-of select="FROM" /></Type>
				<Version><xsl:value-of select="VERSION" /></Version>
				<Publisher><xsl:value-of select="PUBLISHER" /></Publisher>
				<InstallDate><xsl:value-of select="INSTALLDATE" /></InstallDate>
				<Comments><xsl:value-of select="COMMENTS" /></Comments>
				<Size><xsl:value-of select="FILESIZE" /></Size>
				<Folder><xsl:value-of select="FOLDER" /></Folder>
			</Software>
			</xsl:for-each> 

                        <xsl:for-each select="/REQUEST/CONTENT/CONTROLLERS">
			<Controller>
			      	<Name><xsl:value-of select="NAME" /></Name>
			      	<Type><xsl:value-of select="TYPE" /></Type>
			      	<Manufacturer><xsl:value-of select="MANUFACTURER" /></Manufacturer>
			      	<Driver><xsl:value-of select="DRIVER" /></Driver>
			      	<PCIClass><xsl:value-of select="PCICLASS" /></PCIClass>
			      	<PCIId><xsl:value-of select="PCIID" /></PCIId>
			      	<PCISlot><xsl:value-of select="PCISLOT" /></PCISlot>
			</Controller>
                        </xsl:for-each>

                        <xsl:for-each select="/REQUEST/CONTENT/CPUS">
			<Cpu>
			      	<Manufacturer><xsl:value-of select="MANUFACTURER" /></Manufacturer>
			      	<Type><xsl:value-of select="TYPE" /></Type>
			      	<Core><xsl:value-of select="CORE" /></Core>
			      	<Speed><xsl:value-of select="SPEED" /></Speed>
			      	<Serial><xsl:value-of select="SERIAL" /></Serial>
			      	<Thread><xsl:value-of select="THREAD" /></Thread>
			</Cpu>
                        </xsl:for-each>

                        <xsl:for-each select="/REQUEST/CONTENT/DRIVES">
			<Drives>
			      	<Device><xsl:value-of select="VOLUMN" /></Device>
			      	<MountPoint><xsl:value-of select="TYPE" /></MountPoint>
			      	<Filesystem><xsl:value-of select="FILESYSTEM" /></Filesystem>
			      	<Serial><xsl:value-of select="SERIAL" /></Serial>
			      	<Label><xsl:value-of select="LABEL" /></Label>
			      	<CreateDate><xsl:value-of select="CREATEDATE" /></CreateDate>
			      	<TotalSpace><xsl:value-of select="TOTAL" /></TotalSpace>
			      	<FreeSpace><xsl:value-of select="FREE" /></FreeSpace>
			</Drives>
                        </xsl:for-each>

                        <xsl:for-each select="/REQUEST/CONTENT/HARDWARE">
			<Hardware>
				<Name><xsl:value-of select="NAME" /></Name>
				<ArchitectureName><xsl:value-of select="ARCHNAME" /></ArchitectureName>
				<Checksum><xsl:value-of select="CHECKSUM" /></Checksum>
				<DateLastLoggedUser><xsl:value-of select="DATELASTLOGGEDUSER" /></DateLastLoggedUser>
				<LastLoggedUser><xsl:value-of select="LASTLOGGEDUSER" /></LastLoggedUser>
				<DefaultGateway><xsl:value-of select="DEFAULTGATEWAY" /></DefaultGateway>
				<Description><xsl:value-of select="DESCRIPTION" /></Description>
				<IpAddress><xsl:value-of select="IPADDR" /></IpAddress>
				<Memory><xsl:value-of select="MEMORY" /></Memory>
				<OperatingSystemComment><xsl:value-of select="OSCOMMENTS" /></OperatingSystemComment>
				<OperatingSystem><xsl:value-of select="OSNAME" /></OperatingSystem>
				<OperatingSystemVersion><xsl:value-of select="OSVERSION" /></OperatingSystemVersion>
				<UserID><xsl:value-of select="USERID" /></UserID>
				<Processors><xsl:value-of select="PROCESSORN" /></Processors>
				<ProcessorSocket><xsl:value-of select="PROCESSORS" /></ProcessorSocket>
				<ProcessortType><xsl:value-of select="PROCESSORT" /></ProcessortType>
				<SwapMemory><xsl:value-of select="SWAP" /></SwapMemory>
				<VirtualMachineSystem><xsl:value-of select="VMSYSTEM" /></VirtualMachineSystem>
      				<Workgroup><xsl:value-of select="WORKGROUP" /></Workgroup>
				<DNS><xsl:value-of select="DNS" /></DNS>
				<ReportGenerationTime><xsl:value-of select="ETIME" /></ReportGenerationTime>
				<UUID><xsl:value-of select="UUID" /></UUID>
			</Hardware>
                        </xsl:for-each>

                        <xsl:for-each select="/REQUEST/CONTENT/NETWORKS">
			<Network>
				<Description><xsl:value-of select="DESCRIPTION" /></Description>
				<Driver><xsl:value-of select="DRIVER" /></Driver>
				<IpAddress><xsl:value-of select="IPADDRESS" /></IpAddress>
				<DhcpIp><xsl:value-of select="IPDHCP" /></DhcpIp>
				<GatewayIp><xsl:value-of select="IPGATEWAY" /></GatewayIp>
				<SubnetMask><xsl:value-of select="IPMASK" /></SubnetMask>
				<Subnet><xsl:value-of select="IPSUBNET" /></Subnet>
				<MacAddress><xsl:value-of select="MACADDR" /></MacAddress>
				<PCISlot><xsl:value-of select="PCISLOT" /></PCISlot>
				<Slaves><xsl:value-of select="SLAVES" /></Slaves>
				<Status><xsl:value-of select="STATUS" /></Status>
				<Type><xsl:value-of select="TYPE" /></Type>
				<VirtualDevice><xsl:value-of select="VIRTUALDEV" /></VirtualDevice>
			</Network>
			</xsl:for-each>

                        <xsl:for-each select="/REQUEST/CONTENT/PROCESSES">
			<Process>
				<Command><xsl:value-of select="CMD" /></Command>
				<CpuUsage><xsl:value-of select="CPUUSAGE" /></CpuUsage>
				<MemoryUsagePercent><xsl:value-of select="MEM" /></MemoryUsagePercent>
				<StartDate><xsl:value-of select="STARTED" /></StartDate>
				<User><xsl:value-of select="USER" /></User>
				<VirtualMemory><xsl:value-of select="VIRTUALMEMORY" /></VirtualMemory>
				<TTY><xsl:value-of select="TTY" /></TTY>
				<PID><xsl:value-of select="PID" /></PID>
			</Process>
			</xsl:for-each>

		</Event>
        </xsl:template>
</xsl:stylesheet>

