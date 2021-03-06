%bcond_with     connman_openconnect
%bcond_without  connman_openvpn
%bcond_without  connman_vpnd

Name:           connman
Version:        1.29
Release:        14
License:        GPL-2.0+
Summary:        Connection Manager
Url:            http://connman.net
Group:          Network & Connectivity/Connection Management
Source0:        %{name}-%{version}.tar.gz
BuildRequires:  systemd-devel
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(libiptc)
BuildRequires:  pkgconfig(xtables)
BuildRequires:  pkgconfig(libsmack)
BuildRequires:  pkgconfig(tpkp-gnutls)
BuildRequires:  pkgconfig(libsystemd-daemon)
%if %{with connman_openconnect}
BuildRequires:  openconnect
%endif
%if %{with connman_openvpn}
BuildRequires:  openvpn
%endif
BuildRequires:  ca-certificates-devel
BuildRequires:  readline-devel
#%systemd_requires
Requires:       iptables
Requires:         systemd
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
Requires:         net-config

%description
Connection Manager provides a daemon for managing Internet connections
within embedded devices running the Linux operating system.

%if %{with connman_openconnect}
%package plugin-openconnect
Summary:        Openconnect Support for Connman
Requires:       %{name} = %{version}
Requires:       openconnect

%description plugin-openconnect
Openconnect Support for Connman.
%endif

%if %{with connman_openvpn}
%package plugin-openvpn
Summary:        Openvpn Support for Connman
Requires:       %{name} = %{version}
Requires:       openvpn

%description plugin-openvpn
OpenVPN support for Connman.
%endif

%if %{with connman_vpnd}
%package connman-vpnd
Summary:        VPN Support for Connman
#BuildRequires:  %{name} = %{version}
Requires:       %{name} = %{version}

%description connman-vpnd
Provides VPN support for Connman
%endif

%package test
Summary:        Test Scripts for Connection Manager
Group:          Development/Tools
Requires:       %{name} = %{version}
Requires:       dbus-python
Requires:       pygobject
Requires:       python-xml

%description test
Scripts for testing Connman and its functionality

%package devel
Summary:        Development Files for connman
Group:          Development/Tools
Requires:       %{name} = %{version}

%description devel
Header files and development files for connman.

%prep
%setup -q


%build
CFLAGS+=" -DTIZEN_EXT -lsmack -Werror"
CFLAGS+=" -DTIZEN_SYS_CA_BUNDLE=\"%TZ_SYS_RO_CA_BUNDLE\""
%if "%{profile}" == "tv"
CFLAGS+=" -DTIZEN_TV_EXT"
%endif

%if %{with connman_vpnd}
VPN_CFLAGS+=" -DTIZEN_EXT -lsmack -Werror"
%endif

chmod +x bootstrap
./bootstrap
%configure \
            --sysconfdir=/etc \
            --enable-client \
            --enable-pacrunner \
            --enable-wifi=builtin \
%if %{with connman_openconnect}
            --enable-openconnect \
%endif
%if %{with connman_openvpn}
            --enable-openvpn \
%endif
%if 0%{?enable_connman_features}
            %connman_features \
%endif
            --disable-ofono \
            --enable-telephony=builtin \
            --enable-test \
			--enable-loopback \
			--enable-ethernet \
            --with-systemdunitdir=%{_libdir}/systemd/system \
            --enable-pie \
			--disable-wispr

make %{?_smp_mflags}

%install
%make_install

#Systemd service file
mkdir -p %{buildroot}%{_libdir}/systemd/system/
%if "%{?_lib}" == "lib64"
mkdir -p %{buildroot}%{_unitdir}
%endif

%if "%{profile}" == "tv"
cp src/connman_tv.service %{buildroot}%{_libdir}/systemd/system/connman.service
%else
%if "%{?_lib}" == "lib64"
cp src/connman.service %{buildroot}%{_unitdir}/connman.service
cp vpn/connman-vpn.service %{buildroot}%{_unitdir}/connman-vpn.service
%endif
%endif

mkdir -p %{buildroot}%{_libdir}/systemd/system/multi-user.target.wants
ln -s ../connman.service %{buildroot}%{_libdir}/systemd/system/multi-user.target.wants/connman.service
%if "%{?_lib}" == "lib64"
mkdir -p %{buildroot}%{_unitdir}/multi-user.target.wants
ln -s ../connman.service %{buildroot}%{_unitdir}/multi-user.target.wants/connman.service
%endif

mkdir -p %{buildroot}/%{_localstatedir}/lib/connman
cp resources/var/lib/connman/settings %{buildroot}/%{_localstatedir}/lib/connman/settings
mkdir -p %{buildroot}%{_datadir}/dbus-1/system-services
cp resources/usr/share/dbus-1/system-services/net.connman.service %{buildroot}%{_datadir}/dbus-1/system-services/net.connman.service
mkdir -p %{buildroot}/etc/connman
cp src/main.conf %{buildroot}/etc/connman/main.conf

rm %{buildroot}%{_sysconfdir}/dbus-1/system.d/*.conf
mkdir -p %{buildroot}%{_sysconfdir}/dbus-1/system.d/
cp src/connman.conf %{buildroot}%{_sysconfdir}/dbus-1/system.d/

#License
mkdir -p %{buildroot}%{_datadir}/license
cp COPYING %{buildroot}%{_datadir}/license/connman

%if %{with connman_vpnd}
cp vpn/vpn-dbus.conf %{buildroot}%{_sysconfdir}/dbus-1/system.d/connman-vpn-dbus.conf
%endif

%post
chsmack -a 'System' /%{_localstatedir}/lib/connman
chsmack -a 'System' /%{_localstatedir}/lib/connman/settings

%preun

%postun
systemctl daemon-reload

%docs_package

%files
%manifest connman.manifest
%attr(500,root,root) %{_sbindir}/*
%attr(500,root,root) %{_bindir}/connmanctl
%attr(600,root,root) /%{_localstatedir}/lib/connman/settings
#%{_libdir}/connman/plugins/*.so
%attr(644,root,root) %{_datadir}/dbus-1/system-services/*
#%{_datadir}/dbus-1/services/*
%{_sysconfdir}/dbus-1/system.d/*
%attr(644,root,root) %{_sysconfdir}/connman/main.conf
%{_sysconfdir}/dbus-1/system.d/*.conf
%attr(644,root,root) %{_libdir}/systemd/system/connman.service
%attr(644,root,root) %{_libdir}/systemd/system/multi-user.target.wants/connman.service
%attr(644,root,root) %{_libdir}/systemd/system/connman-vpn.service
%if "%{?_lib}" == "lib64"
%attr(644,root,root) %{_unitdir}/connman.service
%attr(644,root,root) %{_unitdir}/multi-user.target.wants/connman.service
%attr(644,root,root) %{_unitdir}/connman-vpn.service
%endif
%{_datadir}/license/connman

%files test
%manifest connman.manifest
%{_libdir}/%{name}/test/*

%files devel
%manifest connman.manifest
%{_includedir}/*
%{_libdir}/pkgconfig/*.pc

%if %{with connman_openconnect}
%files plugin-openconnect
%manifest %{name}.manifest
%{_libdir}/connman/plugins-vpn/openconnect.so
%{_libdir}/connman/scripts/openconnect-script
%{_datadir}/dbus-1/system-services/net.connman.vpn.service
%endif

%if %{with connman_openvpn}
%files plugin-openvpn
%manifest %{name}.manifest
%{_libdir}/%{name}/plugins-vpn/openvpn.so
%{_libdir}/%{name}/scripts/openvpn-script
%{_datadir}/dbus-1/system-services/net.connman.vpn.service
%endif

%if %{with connman_vpnd}
%files connman-vpnd
%manifest %{name}.manifest
#%{_sbindir}/connman-vpnd
%dir %{_libdir}/%{name}
%dir %{_libdir}/%{name}/scripts
%dir %{_libdir}/%{name}/plugins-vpn
%config %{_sysconfdir}/dbus-1/system.d/connman-vpn-dbus.conf
%{_datadir}/dbus-1/system-services/net.connman.vpn.service
%endif


