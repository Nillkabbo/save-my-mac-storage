# Homebrew formula for macOS Cleaner
# Copyright (c) 2026 macOS Cleaner contributors

class MacosCleaner < Formula
  desc "Safe and comprehensive macOS system cleaner with async operations and analytics"
  homepage "https://github.com/mac-cleaner/macos-cleaner"
  url "https://github.com/mac-cleaner/macos-cleaner/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "sha256_placeholder"  # This will be updated during release
  license "MIT"
  head "https://github.com/mac-cleaner/macos-cleaner.git", branch: "main"

  depends_on "python@3.11"

  resource "setuptools" do
    url "https://files.pythonhosted.org/packages/source/s/setuptools/setuptools-68.2.2.tar.gz"
    sha256 "sha256_placeholder"
  end

  resource "wheel" do
    url "https://files.pythonhosted.org/packages/source/w/wheel/wheel-0.41.2.tar.gz"
    sha256 "sha256_placeholder"
  end

  def install
    # Set up Python environment
    python3 = "python3.11"
    venv = libexec/"venv"
    system python3, "-m", "venv", "--system-site-packages", venv

    # Install pip resources
    venv_bin = venv/"bin"
    %w[setuptools wheel].each do |r|
      resource(r).stage do
        system venv_bin/"python", "-m", "pip", "install", "."
      end
    end

    # Install the package
    system venv_bin/"pip", "install", "--prefix=#{libexec}", buildpath

    # Create wrapper scripts
    bin.install venv_bin/"mac-cleaner"
    bin.install venv_bin/"mac-cleaner-gui"
    bin.install venv_bin/"mac-cleaner-web"

    # Install configuration files
    pkgshare.install "src/mac_cleaner/config"
    pkgshare.install "templates"
    pkgshare.install "static"

    # Create launcher script for GUI
    (bin/"mac-cleaner-launcher").write <<~EOS
      #!/bin/bash
      exec "#{bin}/mac-cleaner-gui" "$@"
    EOS

    # Make launcher executable
    chmod 0755, bin/"mac-cleaner-launcher"

    # Install documentation
    doc.install "README.md"
    doc.install "CHANGELOG.md"
    doc.install "USAGE_EXAMPLES.md"
    doc.install "docs"
  end

  def caveats
    <<~EOS
      macOS Cleaner has been installed successfully!

      Available commands:
        mac-cleaner          - Command-line interface
        mac-cleaner-gui      - GUI application
        mac-cleaner-web      - Web interface
        mac-cleaner-launcher - GUI launcher

      Configuration files are located in:
        #{pkgshare}/config/

      For more information, run:
        mac-cleaner --help

      Or visit:
        #{homepage}
    EOS
  end

  test do
    # Test basic functionality
    system bin/"mac-cleaner", "--version"
    system bin/"mac-cleaner", "--help"
    
    # Test that the package is importable
    system libexec/"venv/bin/python", "-c", "import mac_cleaner; print('Import successful')"
  end

  service do
    run [opt_bin/"mac-cleaner-web", "--host", "127.0.0.1", "--port", "5000"]
    keep_alive true
    working_dir Dir.home
    log_path var/"log/mac-cleaner.log"
    error_log_path var/"log/mac-cleaner-error.log"
  end

  # Post-install message
  def post_install
    ohai "macOS Cleaner installation complete!"
    puts "Run 'mac-cleaner --help' to get started."
    puts "For GUI, run 'mac-cleaner-gui' or 'mac-cleaner-launcher'."
    puts "For web interface, run 'mac-cleaner-web'."
  end
end
