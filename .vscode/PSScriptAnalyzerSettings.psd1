@{
    # PSScriptAnalyzer settings for DNDStoryTelling repository

    # Include default rules
    IncludeDefaultRules = $true

    # Exclude rules that might be too restrictive for this project
    ExcludeRules = @(
        'PSAvoidUsingWriteHost',        # We use Write-Host for colored output
        'PSAvoidUsingInvokeExpression', # May be needed for dynamic operations
        'PSUseShouldProcessForStateChangingFunctions' # Not all functions need -WhatIf
    )

    # Custom rules settings
    Rules = @{
        PSPlaceOpenBrace = @{
            Enable = $true
            OnSameLine = $true
            NewLineAfter = $true
            IgnoreOneLineBlock = $true
        }

        PSUseConsistentIndentation = @{
            Enable = $true
            Kind = 'space'
            IndentationSize = 4
        }

        PSUseConsistentWhitespace = @{
            Enable = $true
            CheckOpenBrace = $true
            CheckOpenParen = $true
            CheckOperator = $true
            CheckSeparator = $true
        }

        PSAlignAssignmentStatement = @{
            Enable = $true
            CheckHashtable = $true
        }
    }

    # Severity levels
    Severity = @('Error', 'Warning', 'Information')
}