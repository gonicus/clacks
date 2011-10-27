<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="xml" indent="yes" encoding="UTF-8" />
	<xsl:template match="/">
		<Event xmlns="http://www.gonicus.de/Events">

			<Inventory>
				<DeviceID><xsl:value-of select="/REQUEST/DEVICEID" /></DeviceID>
				<QueryType><xsl:value-of select="/REQUEST/QUERY" /></QueryType>
				<ClientVersion><xsl:value-of select="/REQUEST/CONTENT/VERSIONCLIENT" /></ClientVersion>

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

				<xsl:for-each select="/REQUEST/CONTENT/MODEMS">
					<Modems>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
						<Name><xsl:value-of select="NAME" /></Name>
					</Modems>
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
						<Serial><xsl:value-of select="SERIALNUMBER" /></Serial>
						<Type><xsl:value-of select="TYPE" /></Type>
					</Storage>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/MEMORIES">
					<Memory>
						<Capacity><xsl:value-of select="CAPACITY" /></Capacity>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
						<Caption><xsl:value-of select="CAPTION" /></Caption>
						<Speed><xsl:value-of select="SPEED" /></Speed>
						<Type><xsl:value-of select="TYPE" /></Type>
						<NumberOfSlots><xsl:value-of select="NUMSLOTS" /></NumberOfSlots>
						<Serial><xsl:value-of select="SERIALNUMBER" /></Serial>
					</Memory>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/PORTS">
					<Ports>
						<Caption><xsl:value-of select="CAPTION" /></Caption>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
						<Name><xsl:value-of select="NAME" /></Name>
						<Type><xsl:value-of select="TYPE" /></Type>
					</Ports>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/SLOTS">
					<Slots>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
						<Designation><xsl:value-of select="DESIGNATION" /></Designation>
						<Name><xsl:value-of select="NAME" /></Name>
						<Status><xsl:value-of select="STATUS" /></Status>
					</Slots>
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

				<xsl:for-each select="/REQUEST/CONTENT/MONITORS">
					<Monitor>
						<EDID_Base64><xsl:value-of select="BASE64" /></EDID_Base64>
						<EDID_UUEncode><xsl:value-of select="UUENCODE" /></EDID_UUEncode>
						<Caption><xsl:value-of select="CAPTION" /></Caption>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
						<Manufacturer><xsl:value-of select="MANUFACTURER" /></Manufacturer>
						<Serial><xsl:value-of select="SERIALNUMBER" /></Serial>
					</Monitor>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/VIDEOS">
					<Video>
						<Name><xsl:value-of select="Name" /></Name>
						<Memory><xsl:value-of select="MEMORY" /></Memory>
						<Chipset><xsl:value-of select="CHIPSET" /></Chipset>
						<Resolution><xsl:value-of select="RESOLUTION" /></Resolution>
					</Video>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/SOUNDS">
					<Sound>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
						<Manufacturer><xsl:value-of select="MANUFACTURER" /></Manufacturer>
						<Name><xsl:value-of select="Name" /></Name>
					</Sound>
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
						<ProcessorSpeed><xsl:value-of select="PROCESSORS" /></ProcessorSpeed>
						<ProcessorType><xsl:value-of select="PROCESSORT" /></ProcessorType>
						<SwapMemory><xsl:value-of select="SWAP" /></SwapMemory>
						<VirtualMachineSystem><xsl:value-of select="VMSYSTEM" /></VirtualMachineSystem>
						<Workgroup><xsl:value-of select="WORKGROUP" /></Workgroup>
						<DNS><xsl:value-of select="DNS" /></DNS>
						<ReportGenerationTime><xsl:value-of select="ETIME" /></ReportGenerationTime>
						<Type><xsl:value-of select="TYPE" /></Type>
					</Hardware>
				</xsl:for-each>

				<xsl:for-each select="/REQUEST/CONTENT/BIOS">
					<Bios>
						<BiosDate><xsl:value-of select="BDATE" /></BiosDate>
						<BiosManufacturer><xsl:value-of select="BMANUFACTURER" /></BiosManufacturer>
						<BiosVersion><xsl:value-of select="BVERSION" /></BiosVersion>
						<SystenManufacturer><xsl:value-of select="SMANUFACTURER" /></SystenManufacturer>
						<SystemModel><xsl:value-of select="SMODEL" /></SystemModel>
						<SystemSerial><xsl:value-of select="SSN" /></SystemSerial>
						<BiosAssetTag><xsl:value-of select="ASSETTAG" /></BiosAssetTag>

						<!-- These tags seem to unused right now
						<MMANUFACTURER><xsl:value-of select="MMANUFACTURER" /></MMANUFACTURER>
						<MSN><xsl:value-of select="MSN" /></MSN>
						<MMODEL><xsl:value-of select="MMODEL" /></MMODEL>
						-->
					</Bios>
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

				<xsl:for-each select="/REQUEST/CONTENT/USERS">
					<Users>
						<Login><xsl:value-of select="LOGIN" /></Login>
					</Users>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/PRINTERS">
					<Printer>
						<Description><xsl:value-of select="DESCRIPTION" /></Description>
						<Driver><xsl:value-of select="DRIVER" /></Driver>
						<Name><xsl:value-of select="NAME" /></Name>
						<Port><xsl:value-of select="PORT" /></Port>
					</Printer>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/VIRTUALMACHINES">
					<VirtualMachines>
						<Memory><xsl:value-of select="MEMORY" /></Memory>
						<Name><xsl:value-of select="NAME" /></Name>
						<UUID><xsl:value-of select="UUID" /></UUID>
						<Status><xsl:value-of select="STATUS" /></Status>
						<SubSystem><xsl:value-of select="SUBSYSTEM" /></SubSystem>
						<Type><xsl:value-of select="VMTYPE" /></Type>
						<CPUs><xsl:value-of select="VCPU" /></CPUs>
						<VirtualMachineID><xsl:value-of select="VMID" /></VirtualMachineID>
					</VirtualMachines>
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

				<xsl:for-each select="/REQUEST/CONTENT/ACCESSLOG">
					<AccessLog>
						<LoginDate><xsl:value-of select="LOGDATE" /></LoginDate>
						<UserID><xsl:value-of select="USERID" /></UserID>
					</AccessLog>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/ENVS">
					<Environment>
						<Name><xsl:value-of select="KEY" /></Name>
						<Value><xsl:value-of select="VAL" /></Value>
					</Environment>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/USBDEVICES">
					<USBDevice>
						<Name><xsl:value-of select="NAME" /></Name>
						<VendorID><xsl:value-of select="VENDORID" /></VendorID>
						<ProductID><xsl:value-of select="PRODUCTID" /></ProductID>
						<Serial><xsl:value-of select="SERIAL" /></Serial>
						<Class><xsl:value-of select="CLASS" /></Class>
						<SubClass><xsl:value-of select="SUBCLASS" /></SubClass>
					</USBDevice>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/BATTERIES">
					<Batterie>
						<Name><xsl:value-of select="NAME" /></Name>
						<Serial><xsl:value-of select="SERIAL" /></Serial>
						<Manufacturer><xsl:value-of select="MANUFACTURER" /></Manufacturer>
						<Voltage><xsl:value-of select="VOLTAGE" /></Voltage>
						<Date><xsl:value-of select="DATE" /></Date>
						<Chemistry><xsl:value-of select="CHEMISTRY" /></Chemistry>
						<Capacity><xsl:value-of select="CAPACITY" /></Capacity>
					</Batterie>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/ANTIVIRUS">
					<Antivirus>
						<Company><xsl:value-of select="COMPANY" /></Company>
						<Name><xsl:value-of select="NAME" /></Name>
						<GUID><xsl:value-of select="GUID" /></GUID>
						<Enabled><xsl:value-of select="ENABLED" /></Enabled>
						<UpToDate><xsl:value-of select="UPTODATE" /></UpToDate>
						<Version><xsl:value-of select="VERSION" /></Version>
					</Antivirus>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/LOGICAL_VOLUMES">
					<LogicalVolumes>
						<Name><xsl:value-of select="LV_NAME" /></Name>
						<UUID><xsl:value-of select="LV_UUID" /></UUID>
						<VolumeGroupName><xsl:value-of select="VG_NAME" /></VolumeGroupName>
						<Parameters><xsl:value-of select="ATTR" /></Parameters>
						<Size><xsl:value-of select="SIZE" /></Size>
						<SegmentCount><xsl:value-of select="SEG_COUNT" /></SegmentCount>
					</LogicalVolumes>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/PHYSICAL_VOLUMES">
					<PhysicalVolumes>
						<Device><xsl:value-of select="DEVICE" /></Device>
						<Name><xsl:value-of select="PV_NAME" /></Name>
						<UUID><xsl:value-of select="PV_UUID" /></UUID>
						<Format><xsl:value-of select="FORMAT" /></Format>
						<Parameters><xsl:value-of select="ATTR" /></Parameters>
						<Size><xsl:value-of select="SIZE" /></Size>
						<Free><xsl:value-of select="FREE" /></Free>
						<ExtendSize><xsl:value-of select="PE_SIZE" /></ExtendSize>
						<ExtendCount><xsl:value-of select="PV_PE_COUNT" /></ExtendCount>
					</PhysicalVolumes>
				</xsl:for-each> 

				<xsl:for-each select="/REQUEST/CONTENT/VOLUME_GROUPS">
					<VolumeGroups>
						<Name><xsl:value-of select="VG_NAME" /></Name>
						<PhysicalVolumeCount><xsl:value-of select="PV_COUNT" /></PhysicalVolumeCount>
						<LogicalVolumeCount><xsl:value-of select="LV_COUNT" /></LogicalVolumeCount>
						<Parameters><xsl:value-of select="ATTR" /></Parameters>
						<Size><xsl:value-of select="SIZE" /></Size>
						<Free><xsl:value-of select="FREE" /></Free>
						<UUID><xsl:value-of select="VG_UUID" /></UUID>
						<ExtendSize><xsl:value-of select="VG_EXTENT_SIZE" /></ExtendSize>
					</VolumeGroups>
				</xsl:for-each> 
			</Inventory>
		</Event>
        </xsl:template>
</xsl:stylesheet>
