  - package-ecosystem: pip
    directory: "/"
    schedule:
      interval: weekly
      day: monday
    open-pull-requests-limit: 2
    commit-message:
      prefix: "chore(deps)"
    cooldown:
      default-days: 7
{{ignore}}
    groups:
      python-minor-patch:
        patterns: ["*"]
        update-types: ["minor", "patch"]
