#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, mapper, relationship, backref
from gosa.common.components import AMQPEventConsumer
from lxml import etree

Base = declarative_base()


class Client(Base):

    __tablename__ = 'Client'

    id = Column(Integer, primary_key=True)
    GOsaChecksum = Column(String)
    DeviceID = Column(String)
    QueryType = Column(String)
    ClientVersion = Column(String)


class Controller(Base):

    __tablename__ = 'Controller'

    id = Column(Integer, primary_key=True)
    Name = Column(String)
    Type = Column(String)
    Manufacturer = Column(String)
    Driver = Column(String)
    PCIClass = Column(String)
    PCIID = Column(String)
    PCISlot = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('controller', order_by=id))


class Modem(Base):

    __tablename__ = 'Modem'

    id = Column(Integer, primary_key=True)
    Description = Column(String)
    Name = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('modems', order_by=id))

class Drive(Base):

    __tablename__ = 'Drive'

    id = Column(Integer, primary_key=True)
    Device = Column(String)
    MountPoint = Column(String)
    Filesystem = Column(String)
    Serial = Column(String)
    Label = Column(String)
    CreateDate = Column(String)
    TotalSpace = Column(String)
    FreeSpace = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('drives', order_by=id))

class Storage(Base):

    __tablename__ = 'Storage'

    id = Column(Integer, primary_key=True)
    Description = Column(String)
    DiskSize = Column(String)
    Firmware = Column(String)
    Manufacturer = Column(String)
    Model = Column(String)
    Name = Column(String)
    SCSI_CHID = Column(String)
    SCSI_COID = Column(String)
    SCSI_LUN = Column(String)
    SCSI_UNID = Column(String)
    Serial = Column(String)
    Type = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('storage', order_by=id))

class Memory(Base):

    __tablename__ = 'Memory'

    id = Column(Integer, primary_key=True)
    Capacity = Column(String)
    Description = Column(String)
    Caption = Column(String)
    Speed = Column(String)
    Type = Column(String)
    NumberOfSlots = Column(String)
    Serial = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('memory', order_by=id))

class Port(Base):

    __tablename__ = 'Port'

    id = Column(Integer, primary_key=True)
    Caption = Column(String)
    Description = Column(String)
    Name = Column(String)
    Type = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('ports', order_by=id))


class Slot(Base):

    __tablename__ = 'Slot'

    id = Column(Integer, primary_key=True)
    Description = Column(String)
    Designation = Column(String)
    Name = Column(String)
    Status = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('slots', order_by=id))

class Software (Base):

    __tablename__ = 'Software '

    id = Column(Integer, primary_key=True)
    Name = Column(String)
    Type = Column(String)
    Version = Column(String)
    Publisher = Column(String)
    InstallDate = Column(String)
    Comments = Column(String)
    Size = Column(String)
    Folder = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('software', order_by=id))


class Monitor(Base):

    __tablename__ = 'Monitor'

    id = Column(Integer, primary_key=True)
    EDID_Base64 = Column(String)
    EDID_UUEncode = Column(String)
    Caption = Column(String)
    Description = Column(String)
    Manufacturer = Column(String)
    Serial = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('monitors', order_by=id))


class Video(Base):

    __tablename__ = 'Video'

    id = Column(Integer, primary_key=True)
    Name = Column(String)
    Memory = Column(String)
    Chipset = Column(String)
    Resolution = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('video', order_by=id))


class Sound(Base):

    __tablename__ = 'Sound'

    id = Column(Integer, primary_key=True)
    Description = Column(String)
    Manufacturer = Column(String)
    Name = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('sound', order_by=id))


class Network(Base):

    __tablename__ = 'Network'

    id = Column(Integer, primary_key=True)
    Description = Column(String)
    Driver = Column(String)
    IpAddress = Column(String)
    DhcpIp = Column(String)
    GatewayIp = Column(String)
    SubnetMask = Column(String)
    Subnet = Column(String)
    MacAddress = Column(String)
    PCISlot = Column(String)
    Slaves = Column(String)
    Status = Column(String)
    Type = Column(String)
    VirtualDevice = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('network', order_by=id))


class Hardware(Base):

    __tablename__ = 'Hardware'

    id = Column(Integer, primary_key=True)
    Name = Column(String)
    Architecture = Column(String)
    Checksum = Column(String)
    LastLoggedUser = Column(String)
    DateLastLoggedUser = Column(String)
    DefaultGateway = Column(String)
    Description = Column(String)
    IpAddress = Column(String)
    Memory = Column(String)
    OperatingSystemComment = Column(String)
    OperatingSystem = Column(String)
    OperatingSystemVersion = Column(String)
    UserID = Column(String)
    Processors = Column(String)
    ProcessorSpeed = Column(String)
    ProcessorType = Column(String)
    SwapMemory = Column(String)
    VirtualMachineSystem = Column(String)
    Workgroup = Column(String)
    DNS = Column(String)
    ReportGenerationTime = Column(String)
    Type = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('hardware', order_by=id))


class Bios(Base):

    __tablename__ = 'Bios'

    id = Column(Integer, primary_key=True)
    BiosDate = Column(String)
    BiosManufacturer = Column(String)
    BiosVersion = Column(String)
    SystenManufacturer = Column(String)
    SystemModel = Column(String)
    SystemSerial = Column(String)
    BiosAssetTag = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('bios', order_by=id))


class Cpu(Base):

    __tablename__ = 'Cpu'

    id = Column(Integer, primary_key=True)
    Manufacturer = Column(String)
    Type = Column(String)
    Core = Column(String)
    Speed = Column(String)
    Serial = Column(String)
    Thread = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('cpus', order_by=id))


class Login(Base):

    __tablename__ = 'Login'

    id = Column(Integer, primary_key=True)
    Login = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('logins', order_by=id))

class Printer(Base):

    __tablename__ = 'Printer'

    id = Column(Integer, primary_key=True)
    Description = Column(String)
    Driver = Column(String)
    Name = Column(String)
    Port = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('printers', order_by=id))


class VirtualMachine(Base):

    __tablename__ = 'VirtualMachine'

    id = Column(Integer, primary_key=True)
    Memory = Column(String)
    Name = Column(String)
    UUID = Column(String)
    Status = Column(String)
    SubSystem = Column(String)
    Type = Column(String)
    CPUs = Column(String)
    VirtualMachineID = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('virtual_machines', order_by=id))


class Process(Base):

    __tablename__ = 'Process'

    id = Column(Integer, primary_key=True)
    Command = Column(String)
    CpuUsage = Column(String)
    MemoryUsagePercent = Column(String)
    StartDate = Column(String)
    User = Column(String)
    VirtualMemory = Column(String)
    TTY = Column(String)
    PID = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('processes', order_by=id))


class AccessLog(Base):

    __tablename__ = 'AccessLog'

    id = Column(Integer, primary_key=True)
    LoginDate = Column(String)
    UserID = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('access_log', order_by=id))


class Environment(Base):

    __tablename__ = 'Environment'

    id = Column(Integer, primary_key=True)
    Name = Column(String)
    Value = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('environment', order_by=id))


class USBDevice(Base):

    __tablename__ = 'USBDevice'

    id = Column(Integer, primary_key=True)
    Name = Column(String)
    VendorID = Column(String)
    ProductID = Column(String)
    Serial = Column(String)
    Class = Column(String)
    SubClass = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('usb_devices', order_by=id))


class Batterie(Base):

    __tablename__ = 'Batterie'

    id = Column(Integer, primary_key=True)
    Name = Column(String)
    Serial = Column(String)
    Manufacturer = Column(String)
    Voltage = Column(String)
    Date = Column(String)
    Chemistry = Column(String)
    Capacity = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('batteries', order_by=id))


class Antivirus(Base):

    __tablename__ = 'Antivirus'

    id = Column(Integer, primary_key=True)
    Company = Column(String)
    Name = Column(String)
    GUID = Column(String)
    Enabled = Column(String)
    UpToDate = Column(String)
    Version = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('antivirus', order_by=id))


class LogicalVolume(Base):

    __tablename__ = 'LogicalVolume'

    id = Column(Integer, primary_key=True)
    Name = Column(String)
    UUID = Column(String)
    VolumeGroupName = Column(String)
    Parameters = Column(String)
    Size = Column(String)
    SegmentCount = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('logical_volumes', order_by=id))


class PhysicalVolume(Base):

    __tablename__ = 'PhysicalVolume'

    id = Column(Integer, primary_key=True)
    Device = Column(String)
    Name = Column(String)
    UUID = Column(String)
    Format = Column(String)
    Parameters = Column(String)
    Size = Column(String)
    Free = Column(String)
    ExtendSize = Column(String)
    ExtendCount = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('physical_volumes', order_by=id))

class VolumeGroup(Base):

    __tablename__ = 'VolumeGroup'

    id = Column(Integer, primary_key=True)
    Name = Column(String)
    PhysicalVolumeCount = Column(String)
    LogicalVolumeCount = Column(String)
    Parameters = Column(String)
    Size = Column(String)
    Free = Column(String)
    UUID = Column(String)
    ExtendSize = Column(String)

    client_id = Column(Integer, ForeignKey('Client.id'))
    client = relationship("Client", backref=backref('volume_groups', order_by=id))



