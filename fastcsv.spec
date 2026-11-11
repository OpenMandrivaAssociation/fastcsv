Name:		fastcsv
Version:	4.1.0
Release:	1
Summary:	CSV parser and writer for Java
Group:		Development/Java
License:	MIT
URL:		https://github.com/osiegmar/FastCSV
Source0:	fastcsv-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem

%description
FastCSV %{version} is the CSV library JUnit Jupiter params 6.0.3 compiles
against. Upstream shades it into junit-jupiter-params. This package keeps
the library separate so that jar can require it instead of bundling a copy.
The sources are Java 17 and have no dependencies.

%prep
%autosetup -n FastCSV-%{version} -p1
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
find . -type d -name '*.jar' -print >> binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
find lib/src/main/java -name '*.java' ! -name 'module-info.java' > sources.list
test "$(wc -l < sources.list)" -eq 44
mkdir -p classes
javac --release 17 -encoding UTF-8 -Xlint:-options,-removal -proc:none \
	-d classes @sources.list
echo 'Automatic-Module-Name: de.siegmar.fastcsv' > fastcsv.mf
jar cfm fastcsv.jar fastcsv.mf -C classes .
jar i fastcsv.jar
javap -v -classpath fastcsv.jar de.siegmar.fastcsv.reader.CsvReader | grep -F -q 'major version: 61'
desc=$(jar --describe-module --file fastcsv.jar)
printf '%s\n' "$desc" | grep -F -q 'de.siegmar.fastcsv'
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	exit 1
fi

cat > fastcsv.pom <<END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>de.siegmar</groupId>
  <artifactId>fastcsv</artifactId>
  <version>%{version}</version>
  <name>FastCSV</name>
  <description>CSV parser and writer used by JUnit Jupiter params.</description>
  <url>https://github.com/osiegmar/FastCSV</url>
  <licenses>
    <license>
      <name>MIT</name>
      <url>https://opensource.org/licenses/MIT</url>
      <distribution>repo</distribution>
    </license>
  </licenses>
</project>
END

%install
sysjar install --buildroot %{buildroot} \
	--artifact fastcsv.pom:fastcsv.jar \
	--file-name fastcsv \
	--filelist .mfiles

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
mkdir -p check
cat > check/Smoke.java << 'EOF'
import de.siegmar.fastcsv.reader.CsvReader;
import de.siegmar.fastcsv.reader.CsvRecord;

public class Smoke {
	public static void main(String[] args) throws Exception {
		try (CsvReader<CsvRecord> csv = CsvReader.builder().ofCsvRecord("gradle,fastcsv\n")) {
			CsvRecord rec = csv.iterator().next();
			if (rec.getFieldCount() != 2) {
				throw new AssertionError(rec.getFieldCount());
			}
			System.out.println(args[0] + " " + rec.getField(0) + " " + rec.getField(1) + " " + rec.getFieldCount());
		}
	}
}
EOF
JAR=%{buildroot}%{_javadir}/fastcsv.jar
test -s "$JAR"
javac --release 17 -encoding UTF-8 -proc:none -cp "$JAR" -d check check/Smoke.java
java -cp "check:$JAR" Smoke fastcsv_ok > check/out.txt
cat check/out.txt
grep -F -q 'fastcsv_ok gradle fastcsv 2' check/out.txt

%files -f .mfiles
%doc README.md
%license LICENSE
