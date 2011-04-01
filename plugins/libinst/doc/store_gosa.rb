# cat /usr/lib/ruby/1.8/puppet/reports/store_gosa.rb
require 'puppet'

Puppet::Reports.register_report(:store_gosa) do
  desc "Store the yaml report on disk.  Each host sends its report as a YAML dump
    and this just stores the file on disk, in the `reportdir` directory.

    These files collect quickly -- one every half hour -- so it is a good idea
    to perform some maintenance on them if you use this report (it's the only
    default report)."

  def mkclientdir(client, dir)
    config = Puppet::Util::Settings.new

          config.setdefaults(
        "reportclient-#{client}".to_sym,
      "client-#{client}-dir" => { :default => dir,
        :mode => 02750,
        :desc => "Client dir for #{client}"
      },

      :noop => [false, "Used by settings internally."]
    )

    config.use("reportclient-#{client}".to_sym)
  end

  def process
    # We don't want any tracking back in the fs.  Unlikely, but there
    # you go.
    client = self.host.gsub("..",".")

    dir = File.join(Puppet[:reportdir], client)

    mkclientdir(client, dir) unless FileTest.exists?(dir)

    # Now store the report.
    now = Time.now.gmtime
    name = %w{year month day hour min}.collect do |method|
      # Make sure we're at least two digits everywhere
      "%02d" % now.send(method).to_s
    end.join("") + ".yaml"

    file = File.join(dir, name)

    begin
      File.open(file, "w", 0640) do |f|
        f.print to_yaml
      end
    rescue => detail
      puts detail.backtrace if Puppet[:trace]
      Puppet.warning "Could not write report for #{client} at #{file}: #{detail}"
    end

    # Only testing cares about the return value
    file
  end
end
