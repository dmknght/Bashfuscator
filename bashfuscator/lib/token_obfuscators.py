"""
Token Obfuscators used by the framework.
"""
from binascii import hexlify
import string

from bashfuscator.common.objects import Mutator


class TokenObfuscator(Mutator):
    """
    Base class for all token obfuscators. If an obfuscator is able to
    be deobfuscated and executed by bash at runtime, without bash
    having to execute a stub or any code, then it is a Token Obfuscator.

    :param name: name of the TokenObfuscator
    :type name: str
    :param description: short description of what the TokenObfuscator
        does
    :type description: str
    :param sizeRating: rating from 1 to 5 of how much the 
        TokenObfuscator increases the size of the overall payload
    :type sizeRating: int
    :param notes: see :class:`bashfuscator.common.objects.Mutator`
    :type notes: str
    :param author: see :class:`bashfuscator.common.objects.Mutator`
    :type author: str
    :param credits: see :class:`bashfuscator.common.objects.Mutator`
    :type credits: str
    """

    def __init__(self, name, description, sizeRating, notes=None, author=None, credits=None):
        super().__init__(name, "token", notes, author, credits)

        self.description = description
        self.sizeRating = sizeRating
        self.originalCmd = ""
        self.payload = ""


class AnsiCQuote(TokenObfuscator):
    def __init__(self):
        super().__init__(
            name="ANSI-C Quote",
            description="ANSI-C quotes a string",
            sizeRating=3,
            author="capnspacehook",
            credits="DissectMalware, https://twitter.com/DissectMalware/status/1023682809368653826"
        )

        self.SUBSTR_QUOTE_PROB = 33

    def obfuscate(self, sizePref, userCmd):
        self.originalCmd = userCmd

        obCmd = "printf -- $'\\"

        if sizePref < 2:
            maxChoice = 2
        elif sizePref < 3:
            maxChoice = 3
        else:
            maxChoice = 4

        for char in self.originalCmd:
            choice = self.randGen.randChoice(maxChoice)

            # If sizePref is 3, randomly ANSI-C quote substrings of the original
            # userCmd and randomly add empty strings
            if sizePref == 4 and self.randGen.probibility(self.SUBSTR_QUOTE_PROB):
                obCmd = obCmd[:-1] + "'" + "".join("''" for x in range(
                    self.randGen.randGenNum(0, 5))) + "$'\\"

            if choice == 0:
                obCmd += oct(ord(char))[2:] + "\\"
            elif choice == 1:
                obCmd += hex(ord(char))[1:] + "\\"
            elif choice == 2:
                obCmd += "u00" + hex(ord(char))[2:] + "\\"
            else:
                obCmd += "U000000" + hex(ord(char))[2:] + "\\"

        self.payload = obCmd[:-1] + "'"

        return self.payload


class SpecialCharCommand(TokenObfuscator):
    def __init__(self):
        super().__init__(
            name="Special Char Command",
            description="Converts commands to only use special characters",
            sizeRating=2,
            author="capnspacehook",
            credits="danielbohannon, https://github.com/danielbohannon/Invoke-Obfuscation"
        )

    def obfuscate(self, sizePref, userCmd):
        self.originalCmd = userCmd

        # build list of different commands that will return '0'
        zeroCmdSyntax = [":", "${__}", "_=;", "_=()", "${__[@]}", "${!__[@]}", ":(){ :; };", \
            "_(){ _; };", "_(){ _; };:", "_(){ :; };", "_(){ :; };_", "_(){ :; };:"]

        self.symbols = [" ", "#", "$", "%", "&", "(", ")", "+", ",", "-", ".", "/", ":", ";", "<", "=", ">", "?", "^", "_", "{", "|", "}", "~"]

        zeroCmd = self.randGen.randSelect(zeroCmdSyntax)

        # 1/2 of the time wrap zeroCmd in braces
        if self.randGen.probibility(50):
            if zeroCmd[-1:] != ";":
                zeroCmd += ";"

            zeroCmd = "{ " + zeroCmd + " }"

        initialDigitVar = self.randGen.randUniqueStr(4, 24, "_")

        if self.randGen.probibility(50):
            if zeroCmd[-1:] != ";":
                zeroCmd += ";"

            arrayInstantiationStr = "{0}{1}=$?{2}".format(zeroCmd, initialDigitVar, self.genCommandSeporatorStr())

        else:
            if self.randGen.probibility(50) and zeroCmd[-1:] != ";":
                zeroCmd += ";"

            arrayInstantiationStr = "{0}=`{1}`{2}".format(initialDigitVar, zeroCmd, self.genCommandSeporatorStr())

        incrementSyntaxChoices = ["(({0}={1}++)){2}", "{0}=$(({1}++)){2}", "{0}=$[{1}++]{2}"]
        self.digitVars = []

        for i in range(0, 10):
            self.digitVars.append(self.randGen.randUniqueStr(4, 24, "_"))

            incrementStr = self.randGen.randSelect(incrementSyntaxChoices)
            incrementStr = incrementStr.format(self.digitVars[i], initialDigitVar, self.genCommandSeporatorStr())

            arrayInstantiationStr += incrementStr

        procPIDDirsVar = self.randGen.randUniqueStr(4, 24, "_")
        arrayInstantiationStr += "{0}=(/????/$$/????){1}".format(procPIDDirsVar, self.genCommandSeporatorStr())

        procPIDAttrArrayVar = self.randGen.randUniqueStr(4, 24, "_")
        arrayInstantiationStr += "{0}=${{{1}[${2}]}}{3}".format(procPIDAttrArrayVar, procPIDDirsVar, self.digitVars[0], self.genCommandSeporatorStr())

        procPathArrayVar = self.randGen.randUniqueStr(4, 24, "_")
        arrayInstantiationStr += "{0}=(${{{1}//\// }}){2}".format(procPathArrayVar, procPIDAttrArrayVar, self.genCommandSeporatorStr())

        attrVar = self.randGen.randUniqueStr(4, 24, "_")
        arrayInstantiationStr += "{0}=${{{1}[${2}]}}{3}".format(attrVar, procPathArrayVar, self.digitVars[2], self.genCommandSeporatorStr())

        cattrVar = self.randGen.randUniqueStr(4, 24, "_")
        arrayInstantiationStr += "{0}=${{{1}: -${2}:${2}}}${3}{4}".format(cattrVar, procPathArrayVar, self.digitVars[1], attrVar, self.genCommandSeporatorStr())

        catVar = self.randGen.randUniqueStr(4, 24, "_")
        arrayInstantiationStr += "{0}=${{{1}:{2}:{3}}}{4}".format(catVar, cattrVar, self.digitVars[0], self.digitVars[3], self.genCommandSeporatorStr())

        aVar = self.randGen.randUniqueStr(4, 24, "_")
        arrayInstantiationStr += "{0}=${{{1}:{2}:{3}}}{4}".format(aVar, attrVar, self.digitVars[0], self.digitVars[1], self.genCommandSeporatorStr())

        AVar = self.randGen.randUniqueStr(4, 24, "_")
        arrayInstantiationStr += "{0}=${{{1}^}}{2}".format(AVar, aVar, self.genCommandSeporatorStr())

        fromAtoaVar = self.randGen.randUniqueStr(4, 24, "_")
        arrayInstantiationStr += r". <(${0}<<<{1}=\({{${2}..${3}}}\)){4}".format(catVar, fromAtoaVar, AVar, aVar, self.genCommandSeporatorStr())

        upperAlphabetVar = self.randGen.randUniqueStr(4, 24, "_")
        arrayInstantiationStr += "{0}=(${{{1}[@]:${2}:${3}${4}}}){5}".format(upperAlphabetVar, fromAtoaVar, self.digitVars[0], self.digitVars[2], self.digitVars[6], self.genCommandSeporatorStr())

        lowerAlphabetVar = self.randGen.randUniqueStr(4, 24, "_")
        arrayInstantiationStr += "{0}=(${{{1}[@],,}}){2}".format(lowerAlphabetVar, upperAlphabetVar, self.genCommandSeporatorStr())

        declareVar = self.randGen.randUniqueStr(4, 24, "_")
        arrayInstantiationStr += "{0}={1}{2}".format(declareVar, self.genSymbolAlphabetStr(lowerAlphabetVar, upperAlphabetVar, self.randGen.randSelect(["declare", "typeset"]) + " -A"), self.genCommandSeporatorStr())

        self.mainArrayName = self.randGen.randUniqueStr(3, 5, "_")
        arrayInstantiationStr += "${0} {1}{2}".format(declareVar, self.mainArrayName, self.genCommandSeporatorStr())

        arrayInitializationStrs = []

        evalVar = self.genSymbolVar()
        arrayInstantiationStr += "{0}={1}{2}".format(self.genSetElementStr(evalVar), self.genSymbolAlphabetStr(lowerAlphabetVar, upperAlphabetVar, "eval"), self.genCommandSeporatorStr())

        tempVar = self.genSymbolVar()
        self.digitVars[0] = self.genSymbolVar()
        cmdSubstitutionsStr = "$(:)"
        arrayInstantiationStr += "{0}=`{1} '{{ {2}; }} '${3}'>&'${4}`{5}{6}=${{#{7}}}{8}".format(
            self.genSetElementStr(tempVar), 
            self.genAccessElementStr(evalVar),
            cmdSubstitutionsStr,
            self.digitVars[2],
            self.digitVars[1],
            self.genCommandSeporatorStr(),
            self.genSetElementStr(self.digitVars[0]),
            self.genSetElementStr(tempVar),
            self.genCommandSeporatorStr()
        )

        longOneVar = self.digitVars[1]
        longTwoVar = self.digitVars[2]

        arithemticOperators = ["+", "-"]
        arithmeticExpansionSyntax = ["{0}=$(({1}{2}{3})){4}", "{0}=$[{1}{2}{3}]{4}", "(({0}={1}{2}{3})){4}"]
        for i in range(1, 10):
            newDigitVar = self.genSymbolVar()
            arithmeticSyntax = self.randGen.randSelect(arithmeticExpansionSyntax)

            arrayInitializationStrs.append(arithmeticSyntax.format(
                self.genSetElementStr(newDigitVar), 
                self.digitVars[i],
                self.randGen.randSelect(arithemticOperators),
                self.genSetElementStr(self.digitVars[0]),
                self.genCommandSeporatorStr()
            ))

            self.digitVars[i] = newDigitVar

        catKeyVar = self.genSymbolVar()
        arrayInitializationStrs.append("{0}=${1}{2}".format(self.genSetElementStr(catKeyVar), catVar, self.genCommandSeporatorStr()))
        catVar = catKeyVar

        # TODO: find list of symbol vars that break here
        arrayInitializationStrs.append(": {0} '{{ $[{1}]; }} '${2}'>'{3}{4}".format(
            self.genAccessElementStr(evalVar), 
            self.genAccessElementStr(tempVar), 
            longTwoVar,
            longOneVar,
            self.genCommandSeporatorStr()
        ))

        self.randGen.randShuffle(arrayInitializationStrs)
        arrayInstantiationStr += "".join(arrayInitializationStrs)


        # build the string 'printf' from substrings of error messages
        badStubstitutionErrMsg = " bad substitution"
        badStubstitutionErrVar = self.genSymbolVar()
        badStubstitutionErrStr = "{0}=`{1} '{{ ${{}}; }} '{2}'>&'{3}`{4}{0}=${{{0}##*:}}{5}".format(
            self.genSetElementStr(badStubstitutionErrVar),
            self.genAccessElementStr(evalVar),
            self.genAccessElementStr(self.digitVars[2]),
            self.genAccessElementStr(self.digitVars[1]),
            self.genCommandSeporatorStr(False),
            self.genCommandSeporatorStr()
        )

        noSuchFileOrDirErrSymbols = ["!", "#", "$", "%", "+", ",", "-", ":", "=", "?", "@", "[", "]", "^", "_", "{", "}", "~"]
        noSuchFileOrDirErrCmdSymbol = self.randGen.randSelect(noSuchFileOrDirErrSymbols)
        noSuchFileOrDirErrMsg = " No such file or directory"
        noSuchFileOrDirErrVar = self.genSymbolVar()
        noSuchFileOrDirErrStr = "{0}=`{1} '{{ ./{2}; }} '{3}'>&'{4}`{5}{0}=${{{0}##*:}}{6}".format(
            self.genSetElementStr(noSuchFileOrDirErrVar),
            self.genAccessElementStr(evalVar),
            noSuchFileOrDirErrCmdSymbol,
            self.genAccessElementStr(self.digitVars[2]),
            self.genAccessElementStr(self.digitVars[1]),
            self.genCommandSeporatorStr(False),
            self.genCommandSeporatorStr()
        )

        # get the string 'bash'
        bashStrVar = self.genSymbolVar(bashBracesVar=True)
        bashStr = "{0}=${{{1}:{2}:{3}}}".format(
            self.genSetElementStr(bashStrVar),
            self.genSetElementStr(badStubstitutionErrVar),
            self.genAccessElementStr(self.digitVars[0]),
            self.genAccessElementStr(self.digitVars[3]),
        )

        bashStr += "${{{0}:{1}:{2}}}".format(
            self.genSetElementStr(noSuchFileOrDirErrVar),
            self.genAccessElementStr(self.digitVars[4]),
            self.genAccessElementStr(self.digitVars[1])
        )

        bashStr += "${{{0}:{1}:{2}}}{3}".format(
            self.genSetElementStr(noSuchFileOrDirErrVar),
            self.genAccessElementStr(self.digitVars[7]),
            self.genAccessElementStr(self.digitVars[1]),
            self.genCommandSeporatorStr()
        )

        # get the character 'c' from the 'command not found' error message
        cCharVar = self.genSymbolVar(bashBracesVar=True)
        cCharStr = "{0}=${{{1}:{2}:{3}}}{4}".format(
            self.genSetElementStr(cCharVar),
            self.genSetElementStr(noSuchFileOrDirErrVar),
            self.genAccessElementStr(self.digitVars[6]),
            self.genAccessElementStr(self.digitVars[1]),
            self.genCommandSeporatorStr()
        )

        syntaxErrorMsg = "bash: -c: line 0: syntax error near unexpected token `;' bash: -c: line 0: `;'"
        syntaxErrorVar = self.genSymbolVar()
        syntaxErrorStr = """{0}=`{1} '{{ {2} -{3} ";"; }} '{4}'>&'{5}`{6}""".format(
            self.genSetElementStr(syntaxErrorVar),
            self.genAccessElementStr(evalVar),
            self.genAccessElementStr(bashStrVar),
            self.genAccessElementStr(cCharVar),
            self.genAccessElementStr(self.digitVars[2]),
            self.genAccessElementStr(self.digitVars[1]),
            self.genCommandSeporatorStr(False)
        )

        # get the character 'x' from the 'syntax' error message
        xCharVar = self.genSymbolVar(bashBracesVar=True)
        xCharStr = "{0}=${{{1}:{2}{3}:{4}}}{5}".format(
            self.genSetElementStr(xCharVar),
            self.genSetElementStr(syntaxErrorVar),
            self.genAccessElementStr(self.digitVars[2]),
            self.genAccessElementStr(self.digitVars[3]),
            self.genAccessElementStr(self.digitVars[1]),
            self.genCommandSeporatorStr()
        )

        printfInstanstiationStr = badStubstitutionErrStr + noSuchFileOrDirErrStr + bashStr + cCharStr + syntaxErrorStr + xCharStr


        #store all the possible variations of generating the string 'printf'
        printfCharsInstatiationStrs = []
        printfCharVarNames = {}
        for char in "printf":
            charVars = []

            for errMsg, errVar in [(badStubstitutionErrMsg, badStubstitutionErrVar), (noSuchFileOrDirErrMsg, noSuchFileOrDirErrVar), (syntaxErrorMsg, syntaxErrorVar)]:
                indexes = [i for i, letter in enumerate(errMsg) if letter == char]

                for idx in indexes:
                    charVarName = self.genSymbolVar()

                    digitAccessStr = ""
                    for digit in str(idx):
                        digitAccessStr += self.genAccessElementStr(self.digitVars[int(digit)])

                    printfCharsInstatiationStrs.append("{0}=${{{1}:{2}:{3}}}{4}".format(
                        self.genSetElementStr(charVarName),
                        self.genSetElementStr(errVar),
                        digitAccessStr,
                        self.genAccessElementStr(self.digitVars[1]),
                        self.genCommandSeporatorStr()
                    ))

                    charVars.append(charVarName)

            printfCharVarNames[char] = charVars

        self.randGen.randShuffle(printfCharsInstatiationStrs)
        printfInstanstiationStr += "".join(printfCharsInstatiationStrs)


        # build up 'printf' strings that will print the input and allow it to be executed
        symbolCommandStr = ""
        for cmdChar in userCmd:
            printfStr = ""

            for printfChar in "printf":
                printfStr += self.genAccessElementStr(self.randGen.randSelect(printfCharVarNames[printfChar]))

            digitsAccess = ""
            # if char's hex representation only contains alpha chars, 1/2 of the time use that for the printf statement
            hexCode = str(hex(ord(cmdChar)))[2:]
            if hexCode.isdigit() and self.randGen.probibility(50):
                for char in hexCode:
                    digitsAccess += '"' + self.genAccessElementStr(self.digitVars[int(char)]) + '"'

                symbolCommandStr += r'{0} "\\{1}{2}"'.format(printfStr, self.genAccessElementStr(xCharVar), digitsAccess)

            else:
                octCode = str(oct(ord(cmdChar)))[2:]
                for char in octCode:
                    digitsAccess += '"' + self.genAccessElementStr(self.digitVars[int(char)]) + '"'

                symbolCommandStr += r'{0} "\\{1}"'.format(printfStr, digitsAccess)

            if cmdChar != userCmd[-1]:
                symbolCommandStr += self.genCommandSeporatorStr()

        self.payload = arrayInstantiationStr + printfInstanstiationStr + symbolCommandStr

        return self.payload


    def genCommandSeporatorStr(self, successfulCmd=True):
        cmdSeporators = [";"]
        whitespace = [" ", "\t"]

        #if successfulCmd:
        #    cmdSeporators.append("&&")

        chosenSeporator = self.randGen.randSelect(cmdSeporators)
        #whitespaceAmount = self.randGen.randGenNum(0, 3)
        #randomWhitespace = "".join([self.randGen.randSelect(whitespace) for i in range(whitespaceAmount)])

        return chosenSeporator #+ randomWhitespace

    def genSymbolAlphabetStr(self, lowerArrayName, upperArrayName, initialStr):
        invertSyntaxChoices = ["~", "~~"]
        lowerSyntaxChoices = [",", ",,"] + invertSyntaxChoices
        upperSyntaxChoices = ["^", "^^"] + invertSyntaxChoices

        symbolStr = ""
        for c in initialStr:
            if c in string.punctuation + " ":
                symbolStr += '"{0}"'.format(c)

            elif c in string.ascii_lowercase:
                index = string.ascii_lowercase.find(c)

                indexStr = ""
                for i in str(index):
                    indexStr += "${0}".format(self.digitVars[int(i)])
                
                if self.randGen.probibility(50):
                    symbolStr += "${{{0}[{1}]{2}}}".format(lowerArrayName, indexStr, "")
                else:
                    symbolStr += "${{{0}[{1}]{2}}}".format(upperArrayName, indexStr, self.randGen.randSelect(lowerSyntaxChoices))

            elif c in string.ascii_uppercase:
                index = string.ascii_uppercase.find(c)

                indexStr = ""
                for i in str(index):
                    indexStr += "${0}".format(self.digitVars[int(i)])

                if self.randGen.probibility(50):
                    symbolStr += "${{{0}[{1}]{2}}}".format(upperArrayName, indexStr, "")
                else:
                    symbolStr += "${{{0}[{1}]{2}}}".format(lowerArrayName, indexStr, self.randGen.randSelect(upperSyntaxChoices))

        return symbolStr

    def genAccessElementStr(self, keyVar):
        accessElementStr = '${{{0}["{1}"]}}'.format(self.mainArrayName, keyVar)

        if self.randGen.probibility(50):
            accessElementStr = accessElementStr.replace('"', "'")

        return accessElementStr

    def genSetElementStr(self, keyVar):
        setElementStr = '{0}["{1}"]'.format(self.mainArrayName, keyVar)

        if self.randGen.probibility(50):
            setElementStr = setElementStr.replace('"', "'")

        return setElementStr

    def genSymbolVar(self, min=1, max=3, bashBracesVar=False):
        goodVar = False
        badVars = [" ", "~", "$#", "$$", "$(", "$-", "$?", "$_", "${", ":~", "<(", ">(", "~+", "~-", "~/", "~:", "", "$#", "$$", "$(", "$-", "$?", "$_", "${", ":~", "<(", ">(", "#$#", "#$$", "#$(", "#$-", "#$?", "#$_", "#${", "#:~", "#<(", "#>(", "$#", "$##", "$#$", "$#%", "$#&", "$#(", "$#)", "$#+", "$#,", "$#-", "$#.", "$#/", "$#:", "$#;", "$#<", "$#=", "$#>", "$#?", "$#^", "$#_", "$#{", "$#|", "$#}", "$#~", "$$", "$$#", "$$$", "$$%", "$$&", "$$(", "$$)", "$$+", "$$,", "$$-", "$$.", "$$/", "$$:", "$$;", "$$<", "$$=", "$$>", "$$?", "$$^", "$$_", "$${", "$$|", "$$}", "$$~", "$(", "$(#", "$($", "$(%", "$(&", "$((", "$()", "$(+", "$(,", "$(-", "$(.", "$(/", "$(:", "$(;", "$(<", "$(=", "$(>", "$(?", "$(^", "$(_", "$({", "$(|", "$(}", "$(~", "$-", "$-#", "$-$", "$-%", "$-&", "$-(", "$-)", "$-+", "$-,", "$--", "$-.", "$-/", "$-:", "$-;", "$-<", "$-=", "$->", "$-?", "$-^", "$-_", "$-{", "$-|", "$-}", "$-~", "$:~", "$<(", "$>(", "$?", "$?#", "$?$", "$?%", "$?&", "$?(", "$?)", "$?+", "$?,", "$?-", "$?.", "$?/", "$?:", "$?;", "$?<", "$?=", "$?>", "$??", "$?^", "$?_", "$?{", "$?|", "$?}", "$?~", "$_", "$_#", "$_$", "$_%", "$_&", "$_(", "$_)", "$_+", "$_,", "$_-", "$_.", "$_/", "$_:", "$_;", "$_<", "$_=", "$_>", "$_?", "$_^", "$__", "$_{", "$_|", "$_}", "$_~", "${", "${#", "${$", "${%", "${&", "${(", "${)", "${+", "${,", "${-", "${.", "${/", "${:", "${;", "${<", "${=", "${>", "${?", "${^", "${_", "${{", "${|", "${}", "${~", "%$#", "%$$", "%$(", "%$-", "%$?", "%$_", "%${", "%:~", "%<(", "%>(", "&$#", "&$$", "&$(", "&$-", "&$?", "&$_", "&${", "&:~", "&<(", "&>(", "($#", "($$", "($(", "($-", "($?", "($_", "(${", "(:~", "(<(", "(>(", ")$#", ")$$", ")$(", ")$-", ")$?", ")$_", ")${", "):~", ")<(", ")>(", "+$#", "+$$", "+$(", "+$-", "+$?", "+$_", "+${", "+:~", "+<(", "+>(", ",$#", ",$$", ",$(", ",$-", ",$?", ",$_", ",${", ",:~", ",<(", ",>(", "-$#", "-$$", "-$(", "-$-", "-$?", "-$_", "-${", "-:~", "-<(", "->(", ".$#", ".$$", ".$(", ".$-", ".$?", ".$_", ".${", ".:~", ".<(", ".>(", "/$#", "/$$", "/$(", "/$-", "/$?", "/$_", "/${", "/:~", "/<(", "/>(", ":$#", ":$$", ":$(", ":$-", ":$?", ":$_", ":${", "::~", ":<(", ":>(", ":~+", ":~-", ":~/", ":~:", ";$#", ";$$", ";$(", ";$-", ";$?", ";$_", ";${", ";:~", ";<(", ";>(", "<$#", "<$$", "<$(", "<$-", "<$?", "<$_", "<${", "<(", "<(#", "<($", "<(%", "<(&", "<((", "<()", "<(+", "<(,", "<(-", "<(.", "<(/", "<(:", "<(;", "<(<", "<(=", "<(>", "<(?", "<(^", "<(_", "<({", "<(|", "<(}", "<(~", "<:~", "<<(", "<>(", "=$#", "=$$", "=$(", "=$-", "=$?", "=$_", "=${", "=:~", "=<(", "=>(", ">$#", ">$$", ">$(", ">$-", ">$?", ">$_", ">${", ">(", ">(#", ">($", ">(%", ">(&", ">((", ">()", ">(+", ">(,", ">(-", ">(.", ">(/", ">(:", ">(;", ">(<", ">(=", ">(>", ">(?", ">(^", ">(_", ">({", ">(|", ">(}", ">(~", ">:~", "><(", ">>(", "?$#", "?$$", "?$(", "?$-", "?$?", "?$_", "?${", "?:~", "?<(", "?>(", "^$#", "^$$", "^$(", "^$-", "^$?", "^$_", "^${", "^:~", "^<(", "^>(", "_$#", "_$$", "_$(", "_$-", "_$?", "_$_", "_${", "_:~", "_<(", "_>(", "{$#", "{$$", "{$(", "{$-", "{$?", "{$_", "{${", "{:~", "{<(", "{>(", "|$#", "|$$", "|$(", "|$-", "|$?", "|$_", "|${", "|:~", "|<(", "|>(", "}$#", "}$$", "}$(", "}$-", "}$?", "}$_", "}${", "}:~", "}<(", "}>(", "~$#", "~$$", "~$(", "~$-", "~$?", "~$_", "~${", "~+/", "~+:", "~-/", "~-:", "~/", "~/#", "~/$", "~/%", "~/&", "~/(", "~/)", "~/+", "~/,", "~/-", "~/.", "~//", "~/:", "~/;", "~/<", "~/=", "~/>", "~/?", "~/^", "~/_", "~/{", "~/|", "~/}", "~/~", "~:", "~:#", "~:$", "~:%", "~:&", "~:(", "~:)", "~:+", "~:,", "~:-", "~:.", "~:/", "~::", "~:;", "~:<", "~:=", "~:>", "~:?", "~:^", "~:_", "~:{", "~:|", "~:}", "~:~", "~<(", "~>("]
        badBashVars = [" ", "$", "&", "(", ")", ";", "<", ">", "|", "~", "  ", " #", " $", " &", " (", " )", " ;", " <", " >", " ?", " |", "#$", "#&", "#(", "#)", "#;", "#<", "#>", "#|", "$#", "$$", "$&", "$(", "$)", "$-", "$;", "$<", "$>", "$?", "$_", "${", "$|", "%$", "%&", "%(", "%)", "%;", "%<", "%>", "%|", "& ", "&#", "&$", "&%", "&&", "&(", "&)", "&+", "&,", "&-", "&.", "&/", "&:", "&;", "&<", "&=", "&>", "&?", "&^", "&_", "&{", "&|", "&}", "&~", "( ", "(#", "($", "(%", "(&", "((", "()", "(+", "(,", "(-", "(.", "(/", "(:", "(;", "(<", "(=", "(>", "(?", "(^", "(_", "({", "(|", "(}", "(~", ") ", ")#", ")$", ")%", ")&", ")(", "))", ")+", "),", ")-", ").", ")/", "):", ");", ")<", ")=", ")>", ")?", ")^", ")_", "){", ")|", ")}", ")~", "+$", "+&", "+(", "+)", "+;", "+<", "+>", "+|", ",$", ",&", ",(", ",)", ",;", ",<", ",>", ",|", "-$", "-&", "-(", "-)", "-;", "-<", "->", "-|", ".$", ".&", ".(", ".)", ".;", ".<", ".>", ".|", "/$", "/&", "/(", "/)", "/;", "/<", "/>", "/|", ":$", ":&", ":(", ":)", ":;", ":<", ":>", ":|", ":~", "; ", ";#", ";$", ";%", ";&", ";(", ";)", ";+", ";,", ";-", ";.", ";/", ";:", ";;", ";<", ";=", ";>", ";?", ";^", ";_", ";{", ";|", ";}", ";~", "< ", "<#", "<$", "<%", "<&", "<(", "<)", "<+", "<,", "<-", "<.", "</", "<:", "<;", "<<", "<=", "<>", "<?", "<^", "<_", "<{", "<|", "<}", "<~", "=$", "=&", "=(", "=)", "=;", "=<", "=>", "=|", "> ", ">#", ">$", ">%", ">&", ">(", ">)", ">+", ">,", ">-", ">.", ">/", ">:", ">;", "><", ">=", ">>", ">?", ">^", ">_", ">{", ">|", ">}", ">~", "?$", "?&", "?(", "?)", "?;", "?<", "?>", "?|", "^$", "^&", "^(", "^)", "^;", "^<", "^>", "^|", "_$", "_&", "_(", "_)", "_;", "_<", "_>", "_|", "{$", "{&", "{(", "{)", "{;", "{<", "{>", "{|", "| ", "|#", "|$", "|%", "|&", "|(", "|)", "|+", "|,", "|-", "|.", "|/", "|:", "|;", "|<", "|=", "|>", "|?", "|^", "|_", "|{", "||", "|}", "|~", "} ", "}$", "}&", "}(", "})", "};", "}<", "}>", "}|", "~$", "~&", "~(", "~)", "~+", "~-", "~/", "~:", "~;", "~<", "~>", "~|", "   ", "  #", "  $", "  %", "  &", "  (", "  )", "  +", "  ,", "  -", "  .", "  /", "  :", "  ;", "  <", "  =", "  >", "  ?", "  ^", "  _", "  {", "  |", "  }", "  ~", " # ", " ##", " #$", " #%", " #&", " #(", " #)", " #+", " #,", " #-", " #.", " #/", " #:", " #;", " #<", " #=", " #>", " #?", " #^", " #_", " #{", " #|", " #}", " #~", " $#", " $$", " $&", " $(", " $)", " $-", " $;", " $<", " $>", " $?", " $_", " ${", " $|", " %$", " %&", " %(", " %)", " %;", " %<", " %>", " %?", " %|", " & ", " &#", " &$", " &%", " &&", " &(", " &)", " &+", " &,", " &-", " &.", " &/", " &:", " &;", " &<", " &=", " &>", " &?", " &^", " &_", " &{", " &|", " &}", " &~", " ( ", " (#", " ($", " (%", " (&", " ((", " ()", " (+", " (,", " (-", " (.", " (/", " (:", " (;", " (<", " (=", " (>", " (?", " (^", " (_", " ({", " (|", " (}", " (~", " ) ", " )#", " )$", " )%", " )&", " )(", " ))", " )+", " ),", " )-", " ).", " )/", " ):", " );", " )<", " )=", " )>", " )?", " )^", " )_", " ){", " )|", " )}", " )~", " +$", " +&", " +(", " +)", " +;", " +<", " +>", " +?", " +|", " ,$", " ,&", " ,(", " ,)", " ,;", " ,<", " ,>", " ,?", " ,|", " -$", " -&", " -(", " -)", " -;", " -<", " ->", " -?", " -|", " .$", " .&", " .(", " .)", " .;", " .<", " .>", " .?", " .|", " /$", " /&", " /(", " /)", " /;", " /<", " />", " /|", " :$", " :&", " :(", " :)", " :;", " :<", " :>", " :?", " :|", " :~", " ; ", " ;#", " ;$", " ;%", " ;&", " ;(", " ;)", " ;+", " ;,", " ;-", " ;.", " ;/", " ;:", " ;;", " ;<", " ;=", " ;>", " ;?", " ;^", " ;_", " ;{", " ;|", " ;}", " ;~", " < ", " <#", " <$", " <%", " <&", " <(", " <)", " <+", " <,", " <-", " <.", " </", " <:", " <;", " <<", " <=", " <>", " <?", " <^", " <_", " <{", " <|", " <}", " <~", " =$", " =&", " =(", " =)", " =;", " =<", " =>", " =?", " =|", " > ", " >#", " >$", " >%", " >&", " >(", " >)", " >+", " >,", " >-", " >.", " >/", " >:", " >;", " ><", " >=", " >>", " >?", " >^", " >_", " >{", " >|", " >}", " >~", " ? ", " ?#", " ?$", " ?%", " ?&", " ?(", " ?)", " ?+", " ?,", " ?-", " ?.", " ?:", " ?;", " ?<", " ?=", " ?>", " ??", " ?^", " ?_", " ?{", " ?|", " ?}", " ?~", " ^$", " ^&", " ^(", " ^)", " ^;", " ^<", " ^>", " ^?", " ^|", " _$", " _&", " _(", " _)", " _;", " _<", " _>", " _?", " _|", " {$", " {&", " {(", " {)", " {;", " {<", " {>", " {?", " {|", " | ", " |#", " |$", " |%", " |&", " |(", " |)", " |+", " |,", " |-", " |.", " |/", " |:", " |;", " |<", " |=", " |>", " |?", " |^", " |_", " |{", " ||", " |}", " |~", " } ", " }$", " }&", " }(", " })", " };", " }<", " }>", " }?", " }|", " ~ ", " ~$", " ~&", " ~(", " ~)", " ~/", " ~;", " ~<", " ~>", " ~?", " ~|", "#  ", "# #", "# $", "# &", "# (", "# )", "# ;", "# <", "# >", "# ?", "# |", "##$", "##&", "##(", "##)", "##;", "##<", "##>", "##|", "#$#", "#$$", "#$&", "#$(", "#$)", "#$-", "#$;", "#$<", "#$>", "#$?", "#$_", "#${", "#$|", "#%$", "#%&", "#%(", "#%)", "#%;", "#%<", "#%>", "#%|", "#& ", "#&#", "#&$", "#&%", "#&&", "#&(", "#&)", "#&+", "#&,", "#&-", "#&.", "#&/", "#&:", "#&;", "#&<", "#&=", "#&>", "#&?", "#&^", "#&_", "#&{", "#&|", "#&}", "#&~", "#( ", "#(#", "#($", "#(%", "#(&", "#((", "#()", "#(+", "#(,", "#(-", "#(.", "#(/", "#(:", "#(;", "#(<", "#(=", "#(>", "#(?", "#(^", "#(_", "#({", "#(|", "#(}", "#(~", "#) ", "#)#", "#)$", "#)%", "#)&", "#)(", "#))", "#)+", "#),", "#)-", "#).", "#)/", "#):", "#);", "#)<", "#)=", "#)>", "#)?", "#)^", "#)_", "#){", "#)|", "#)}", "#)~", "#+$", "#+&", "#+(", "#+)", "#+;", "#+<", "#+>", "#+|", "#,$", "#,&", "#,(", "#,)", "#,;", "#,<", "#,>", "#,|", "#-$", "#-&", "#-(", "#-)", "#-;", "#-<", "#->", "#-|", "#.$", "#.&", "#.(", "#.)", "#.;", "#.<", "#.>", "#.|", "#/$", "#/&", "#/(", "#/)", "#/;", "#/<", "#/>", "#/|", "#:$", "#:&", "#:(", "#:)", "#:;", "#:<", "#:>", "#:|", "#:~", "#; ", "#;#", "#;$", "#;%", "#;&", "#;(", "#;)", "#;+", "#;,", "#;-", "#;.", "#;/", "#;:", "#;;", "#;<", "#;=", "#;>", "#;?", "#;^", "#;_", "#;{", "#;|", "#;}", "#;~", "#< ", "#<#", "#<$", "#<%", "#<&", "#<(", "#<)", "#<+", "#<,", "#<-", "#<.", "#</", "#<:", "#<;", "#<<", "#<=", "#<>", "#<?", "#<^", "#<_", "#<{", "#<|", "#<}", "#<~", "#=$", "#=&", "#=(", "#=)", "#=;", "#=<", "#=>", "#=|", "#> ", "#>#", "#>$", "#>%", "#>&", "#>(", "#>)", "#>+", "#>,", "#>-", "#>.", "#>/", "#>:", "#>;", "#><", "#>=", "#>>", "#>?", "#>^", "#>_", "#>{", "#>|", "#>}", "#>~", "#?$", "#?&", "#?(", "#?)", "#?;", "#?<", "#?>", "#?|", "#^$", "#^&", "#^(", "#^)", "#^;", "#^<", "#^>", "#^|", "#_$", "#_&", "#_(", "#_)", "#_;", "#_<", "#_>", "#_|", "#{$", "#{&", "#{(", "#{)", "#{;", "#{<", "#{>", "#{|", "#| ", "#|#", "#|$", "#|%", "#|&", "#|(", "#|)", "#|+", "#|,", "#|-", "#|.", "#|/", "#|:", "#|;", "#|<", "#|=", "#|>", "#|?", "#|^", "#|_", "#|{", "#||", "#|}", "#|~", "#} ", "#}$", "#}&", "#}(", "#})", "#};", "#}<", "#}>", "#}|", "#~$", "#~&", "#~(", "#~)", "#~;", "#~<", "#~>", "#~|", "$  ", "$ #", "$ $", "$ &", "$ (", "$ )", "$ ;", "$ <", "$ >", "$ ?", "$ |", "$# ", "$##", "$#$", "$#%", "$#&", "$#(", "$#)", "$#+", "$#,", "$#-", "$#.", "$#/", "$#:", "$#;", "$#<", "$#=", "$#>", "$#?", "$#^", "$#_", "$#{", "$#|", "$#}", "$#~", "$$ ", "$$#", "$$$", "$$%", "$$&", "$$(", "$$)", "$$+", "$$,", "$$-", "$$.", "$$/", "$$:", "$$;", "$$<", "$$=", "$$>", "$$?", "$$^", "$$_", "$${", "$$|", "$$}", "$$~", "$%$", "$%&", "$%(", "$%)", "$%;", "$%<", "$%>", "$%|", "$& ", "$&#", "$&$", "$&%", "$&&", "$&(", "$&)", "$&+", "$&,", "$&-", "$&.", "$&/", "$&:", "$&;", "$&<", "$&=", "$&>", "$&?", "$&^", "$&_", "$&{", "$&|", "$&}", "$&~", "$( ", "$(#", "$($", "$(%", "$(&", "$((", "$()", "$(+", "$(,", "$(-", "$(.", "$(/", "$(:", "$(;", "$(<", "$(=", "$(>", "$(?", "$(^", "$(_", "$({", "$(|", "$(}", "$(~", "$) ", "$)#", "$)$", "$)%", "$)&", "$)(", "$))", "$)+", "$),", "$)-", "$).", "$)/", "$):", "$);", "$)<", "$)=", "$)>", "$)?", "$)^", "$)_", "$){", "$)|", "$)}", "$)~", "$+$", "$+&", "$+(", "$+)", "$+;", "$+<", "$+>", "$+|", "$,$", "$,&", "$,(", "$,)", "$,;", "$,<", "$,>", "$,|", "$- ", "$-#", "$-$", "$-%", "$-&", "$-(", "$-)", "$-+", "$-,", "$--", "$-.", "$-/", "$-:", "$-;", "$-<", "$-=", "$->", "$-?", "$-^", "$-_", "$-{", "$-|", "$-}", "$-~", "$.$", "$.&", "$.(", "$.)", "$.;", "$.<", "$.>", "$.|", "$/$", "$/&", "$/(", "$/)", "$/;", "$/<", "$/>", "$/|", "$:$", "$:&", "$:(", "$:)", "$:;", "$:<", "$:>", "$:|", "$:~", "$; ", "$;#", "$;$", "$;%", "$;&", "$;(", "$;)", "$;+", "$;,", "$;-", "$;.", "$;/", "$;:", "$;;", "$;<", "$;=", "$;>", "$;?", "$;^", "$;_", "$;{", "$;|", "$;}", "$;~", "$< ", "$<#", "$<$", "$<%", "$<&", "$<(", "$<)", "$<+", "$<,", "$<-", "$<.", "$</", "$<:", "$<;", "$<<", "$<=", "$<>", "$<?", "$<^", "$<_", "$<{", "$<|", "$<}", "$<~", "$=$", "$=&", "$=(", "$=)", "$=;", "$=<", "$=>", "$=|", "$> ", "$>#", "$>$", "$>%", "$>&", "$>(", "$>)", "$>+", "$>,", "$>-", "$>.", "$>/", "$>:", "$>;", "$><", "$>=", "$>>", "$>?", "$>^", "$>_", "$>{", "$>|", "$>}", "$>~", "$? ", "$?#", "$?$", "$?%", "$?&", "$?(", "$?)", "$?+", "$?,", "$?-", "$?.", "$?/", "$?:", "$?;", "$?<", "$?=", "$?>", "$??", "$?^", "$?_", "$?{", "$?|", "$?}", "$?~", "$^$", "$^&", "$^(", "$^)", "$^;", "$^<", "$^>", "$^|", "$_ ", "$_#", "$_$", "$_%", "$_&", "$_(", "$_)", "$_+", "$_,", "$_-", "$_.", "$_/", "$_:", "$_;", "$_<", "$_=", "$_>", "$_?", "$_^", "$__", "$_{", "$_|", "$_}", "$_~", "${ ", "${#", "${$", "${%", "${&", "${(", "${)", "${+", "${,", "${-", "${.", "${/", "${:", "${;", "${<", "${=", "${>", "${?", "${^", "${_", "${{", "${|", "${}", "${~", "$| ", "$|#", "$|$", "$|%", "$|&", "$|(", "$|)", "$|+", "$|,", "$|-", "$|.", "$|/", "$|:", "$|;", "$|<", "$|=", "$|>", "$|?", "$|^", "$|_", "$|{", "$||", "$|}", "$|~", "$} ", "$}$", "$}&", "$}(", "$})", "$};", "$}<", "$}>", "$}|", "$~$", "$~&", "$~(", "$~)", "$~;", "$~<", "$~>", "$~|", "%  ", "% #", "% $", "% &", "% (", "% )", "% ;", "% <", "% >", "% ?", "% |", "%#$", "%#&", "%#(", "%#)", "%#;", "%#<", "%#>", "%#|", "%$#", "%$$", "%$&", "%$(", "%$)", "%$-", "%$;", "%$<", "%$>", "%$?", "%$_", "%${", "%$|", "%%$", "%%&", "%%(", "%%)", "%%;", "%%<", "%%>", "%%|", "%& ", "%&#", "%&$", "%&%", "%&&", "%&(", "%&)", "%&+", "%&,", "%&-", "%&.", "%&/", "%&:", "%&;", "%&<", "%&=", "%&>", "%&?", "%&^", "%&_", "%&{", "%&|", "%&}", "%&~", "%( ", "%(#", "%($", "%(%", "%(&", "%((", "%()", "%(+", "%(,", "%(-", "%(.", "%(/", "%(:", "%(;", "%(<", "%(=", "%(>", "%(?", "%(^", "%(_", "%({", "%(|", "%(}", "%(~", "%) ", "%)#", "%)$", "%)%", "%)&", "%)(", "%))", "%)+", "%),", "%)-", "%).", "%)/", "%):", "%);", "%)<", "%)=", "%)>", "%)?", "%)^", "%)_", "%){", "%)|", "%)}", "%)~", "%+$", "%+&", "%+(", "%+)", "%+;", "%+<", "%+>", "%+|", "%,$", "%,&", "%,(", "%,)", "%,;", "%,<", "%,>", "%,|", "%-$", "%-&", "%-(", "%-)", "%-;", "%-<", "%->", "%-|", "%.$", "%.&", "%.(", "%.)", "%.;", "%.<", "%.>", "%.|", "%/$", "%/&", "%/(", "%/)", "%/;", "%/<", "%/>", "%/|", "%:$", "%:&", "%:(", "%:)", "%:;", "%:<", "%:>", "%:|", "%:~", "%; ", "%;#", "%;$", "%;%", "%;&", "%;(", "%;)", "%;+", "%;,", "%;-", "%;.", "%;/", "%;:", "%;;", "%;<", "%;=", "%;>", "%;?", "%;^", "%;_", "%;{", "%;|", "%;}", "%;~", "%< ", "%<#", "%<$", "%<%", "%<&", "%<(", "%<)", "%<+", "%<,", "%<-", "%<.", "%</", "%<:", "%<;", "%<<", "%<=", "%<>", "%<?", "%<^", "%<_", "%<{", "%<|", "%<}", "%<~", "%=$", "%=&", "%=(", "%=)", "%=;", "%=<", "%=>", "%=|", "%> ", "%>#", "%>$", "%>%", "%>&", "%>(", "%>)", "%>+", "%>,", "%>-", "%>.", "%>/", "%>:", "%>;", "%><", "%>=", "%>>", "%>?", "%>^", "%>_", "%>{", "%>|", "%>}", "%>~", "%?$", "%?&", "%?(", "%?)", "%?;", "%?<", "%?>", "%?|", "%^$", "%^&", "%^(", "%^)", "%^;", "%^<", "%^>", "%^|", "%_$", "%_&", "%_(", "%_)", "%_;", "%_<", "%_>", "%_|", "%{$", "%{&", "%{(", "%{)", "%{;", "%{<", "%{>", "%{|", "%| ", "%|#", "%|$", "%|%", "%|&", "%|(", "%|)", "%|+", "%|,", "%|-", "%|.", "%|/", "%|:", "%|;", "%|<", "%|=", "%|>", "%|?", "%|^", "%|_", "%|{", "%||", "%|}", "%|~", "%} ", "%}$", "%}&", "%}(", "%})", "%};", "%}<", "%}>", "%}|", "%~$", "%~&", "%~(", "%~)", "%~;", "%~<", "%~>", "%~|", "&  ", "& #", "& $", "& %", "& &", "& (", "& )", "& +", "& ,", "& -", "& .", "& /", "& :", "& ;", "& <", "& =", "& >", "& ?", "& ^", "& _", "& {", "& |", "& }", "& ~", "&# ", "&##", "&#$", "&#%", "&#&", "&#(", "&#)", "&#+", "&#,", "&#-", "&#.", "&#/", "&#:", "&#;", "&#<", "&#=", "&#>", "&#?", "&#^", "&#_", "&#{", "&#|", "&#}", "&#~", "&$ ", "&$#", "&$$", "&$%", "&$&", "&$(", "&$)", "&$+", "&$,", "&$-", "&$.", "&$/", "&$:", "&$;", "&$<", "&$=", "&$>", "&$?", "&$^", "&$_", "&${", "&$|", "&$}", "&$~", "&% ", "&%#", "&%$", "&%%", "&%&", "&%(", "&%)", "&%+", "&%,", "&%-", "&%.", "&%/", "&%:", "&%;", "&%<", "&%=", "&%>", "&%?", "&%^", "&%_", "&%{", "&%|", "&%}", "&%~", "&& ", "&&#", "&&$", "&&%", "&&&", "&&(", "&&)", "&&+", "&&,", "&&-", "&&.", "&&/", "&&:", "&&;", "&&<", "&&=", "&&>", "&&?", "&&^", "&&_", "&&{", "&&|", "&&}", "&&~", "&( ", "&(#", "&($", "&(%", "&(&", "&((", "&()", "&(+", "&(,", "&(-", "&(.", "&(/", "&(:", "&(;", "&(<", "&(=", "&(>", "&(?", "&(^", "&(_", "&({", "&(|", "&(}", "&(~", "&) ", "&)#", "&)$", "&)%", "&)&", "&)(", "&))", "&)+", "&),", "&)-", "&).", "&)/", "&):", "&);", "&)<", "&)=", "&)>", "&)?", "&)^", "&)_", "&){", "&)|", "&)}", "&)~", "&+ ", "&+#", "&+$", "&+%", "&+&", "&+(", "&+)", "&++", "&+,", "&+-", "&+.", "&+/", "&+:", "&+;", "&+<", "&+=", "&+>", "&+?", "&+^", "&+_", "&+{", "&+|", "&+}", "&+~", "&, ", "&,#", "&,$", "&,%", "&,&", "&,(", "&,)", "&,+", "&,,", "&,-", "&,.", "&,/", "&,:", "&,;", "&,<", "&,=", "&,>", "&,?", "&,^", "&,_", "&,{", "&,|", "&,}", "&,~", "&- ", "&-#", "&-$", "&-%", "&-&", "&-(", "&-)", "&-+", "&-,", "&--", "&-.", "&-/", "&-:", "&-;", "&-<", "&-=", "&->", "&-?", "&-^", "&-_", "&-{", "&-|", "&-}", "&-~", "&. ", "&.#", "&.$", "&.%", "&.&", "&.(", "&.)", "&.+", "&.,", "&.-", "&..", "&./", "&.:", "&.;", "&.<", "&.=", "&.>", "&.?", "&.^", "&._", "&.{", "&.|", "&.}", "&.~", "&/ ", "&/#", "&/$", "&/%", "&/&", "&/(", "&/)", "&/+", "&/,", "&/-", "&/.", "&//", "&/:", "&/;", "&/<", "&/=", "&/>", "&/?", "&/^", "&/_", "&/{", "&/|", "&/}", "&/~", "&: ", "&:#", "&:$", "&:%", "&:&", "&:(", "&:)", "&:+", "&:,", "&:-", "&:.", "&:/", "&::", "&:;", "&:<", "&:=", "&:>", "&:?", "&:^", "&:_", "&:{", "&:|", "&:}", "&:~", "&; ", "&;#", "&;$", "&;%", "&;&", "&;(", "&;)", "&;+", "&;,", "&;-", "&;.", "&;/", "&;:", "&;;", "&;<", "&;=", "&;>", "&;?", "&;^", "&;_", "&;{", "&;|", "&;}", "&;~", "&< ", "&<#", "&<$", "&<%", "&<&", "&<(", "&<)", "&<+", "&<,", "&<-", "&<.", "&</", "&<:", "&<;", "&<<", "&<=", "&<>", "&<?", "&<^", "&<_", "&<{", "&<|", "&<}", "&<~", "&= ", "&=#", "&=$", "&=%", "&=&", "&=(", "&=)", "&=+", "&=,", "&=-", "&=.", "&=/", "&=:", "&=;", "&=<", "&==", "&=>", "&=?", "&=^", "&=_", "&={", "&=|", "&=}", "&=~", "&> ", "&>#", "&>$", "&>%", "&>&", "&>(", "&>)", "&>+", "&>,", "&>-", "&>.", "&>/", "&>:", "&>;", "&><", "&>=", "&>>", "&>?", "&>^", "&>_", "&>{", "&>|", "&>}", "&>~", "&? ", "&?#", "&?$", "&?%", "&?&", "&?(", "&?)", "&?+", "&?,", "&?-", "&?.", "&?/", "&?:", "&?;", "&?<", "&?=", "&?>", "&??", "&?^", "&?_", "&?{", "&?|", "&?}", "&?~", "&^ ", "&^#", "&^$", "&^%", "&^&", "&^(", "&^)", "&^+", "&^,", "&^-", "&^.", "&^/", "&^:", "&^;", "&^<", "&^=", "&^>", "&^?", "&^^", "&^_", "&^{", "&^|", "&^}", "&^~", "&_ ", "&_#", "&_$", "&_%", "&_&", "&_(", "&_)", "&_+", "&_,", "&_-", "&_.", "&_/", "&_:", "&_;", "&_<", "&_=", "&_>", "&_?", "&_^", "&__", "&_{", "&_|", "&_}", "&_~", "&{ ", "&{#", "&{$", "&{%", "&{&", "&{(", "&{)", "&{+", "&{,", "&{-", "&{.", "&{/", "&{:", "&{;", "&{<", "&{=", "&{>", "&{?", "&{^", "&{_", "&{{", "&{|", "&{}", "&{~", "&| ", "&|#", "&|$", "&|%", "&|&", "&|(", "&|)", "&|+", "&|,", "&|-", "&|.", "&|/", "&|:", "&|;", "&|<", "&|=", "&|>", "&|?", "&|^", "&|_", "&|{", "&||", "&|}", "&|~", "&} ", "&}#", "&}$", "&}%", "&}&", "&}(", "&})", "&}+", "&},", "&}-", "&}.", "&}/", "&}:", "&};", "&}<", "&}=", "&}>", "&}?", "&}^", "&}_", "&}{", "&}|", "&}}", "&}~", "&~ ", "&~#", "&~$", "&~%", "&~&", "&~(", "&~)", "&~+", "&~,", "&~-", "&~.", "&~/", "&~:", "&~;", "&~<", "&~=", "&~>", "&~?", "&~^", "&~_", "&~{", "&~|", "&~}", "&~~", "(  ", "( #", "( $", "( %", "( &", "( (", "( )", "( +", "( ,", "( -", "( .", "( /", "( :", "( ;", "( <", "( =", "( >", "( ?", "( ^", "( _", "( {", "( |", "( }", "( ~", "(# ", "(##", "(#$", "(#%", "(#&", "(#(", "(#)", "(#+", "(#,", "(#-", "(#.", "(#/", "(#:", "(#;", "(#<", "(#=", "(#>", "(#?", "(#^", "(#_", "(#{", "(#|", "(#}", "(#~", "($ ", "($#", "($$", "($%", "($&", "($(", "($)", "($+", "($,", "($-", "($.", "($/", "($:", "($;", "($<", "($=", "($>", "($?", "($^", "($_", "(${", "($|", "($}", "($~", "(% ", "(%#", "(%$", "(%%", "(%&", "(%(", "(%)", "(%+", "(%,", "(%-", "(%.", "(%/", "(%:", "(%;", "(%<", "(%=", "(%>", "(%?", "(%^", "(%_", "(%{", "(%|", "(%}", "(%~", "(& ", "(&#", "(&$", "(&%", "(&&", "(&(", "(&)", "(&+", "(&,", "(&-", "(&.", "(&/", "(&:", "(&;", "(&<", "(&=", "(&>", "(&?", "(&^", "(&_", "(&{", "(&|", "(&}", "(&~", "(( ", "((#", "(($", "((%", "((&", "(((", "(()", "((+", "((,", "((-", "((.", "((/", "((:", "((;", "((<", "((=", "((>", "((?", "((^", "((_", "(({", "((|", "((}", "((~", "() ", "()#", "()$", "()%", "()&", "()(", "())", "()+", "(),", "()-", "().", "()/", "():", "();", "()<", "()=", "()>", "()?", "()^", "()_", "(){", "()|", "()}", "()~", "(+ ", "(+#", "(+$", "(+%", "(+&", "(+(", "(+)", "(++", "(+,", "(+-", "(+.", "(+/", "(+:", "(+;", "(+<", "(+=", "(+>", "(+?", "(+^", "(+_", "(+{", "(+|", "(+}", "(+~", "(, ", "(,#", "(,$", "(,%", "(,&", "(,(", "(,)", "(,+", "(,,", "(,-", "(,.", "(,/", "(,:", "(,;", "(,<", "(,=", "(,>", "(,?", "(,^", "(,_", "(,{", "(,|", "(,}", "(,~", "(- ", "(-#", "(-$", "(-%", "(-&", "(-(", "(-)", "(-+", "(-,", "(--", "(-.", "(-/", "(-:", "(-;", "(-<", "(-=", "(->", "(-?", "(-^", "(-_", "(-{", "(-|", "(-}", "(-~", "(. ", "(.#", "(.$", "(.%", "(.&", "(.(", "(.)", "(.+", "(.,", "(.-", "(..", "(./", "(.:", "(.;", "(.<", "(.=", "(.>", "(.?", "(.^", "(._", "(.{", "(.|", "(.}", "(.~", "(/ ", "(/#", "(/$", "(/%", "(/&", "(/(", "(/)", "(/+", "(/,", "(/-", "(/.", "(//", "(/:", "(/;", "(/<", "(/=", "(/>", "(/?", "(/^", "(/_", "(/{", "(/|", "(/}", "(/~", "(: ", "(:#", "(:$", "(:%", "(:&", "(:(", "(:)", "(:+", "(:,", "(:-", "(:.", "(:/", "(::", "(:;", "(:<", "(:=", "(:>", "(:?", "(:^", "(:_", "(:{", "(:|", "(:}", "(:~", "(; ", "(;#", "(;$", "(;%", "(;&", "(;(", "(;)", "(;+", "(;,", "(;-", "(;.", "(;/", "(;:", "(;;", "(;<", "(;=", "(;>", "(;?", "(;^", "(;_", "(;{", "(;|", "(;}", "(;~", "(< ", "(<#", "(<$", "(<%", "(<&", "(<(", "(<)", "(<+", "(<,", "(<-", "(<.", "(</", "(<:", "(<;", "(<<", "(<=", "(<>", "(<?", "(<^", "(<_", "(<{", "(<|", "(<}", "(<~", "(= ", "(=#", "(=$", "(=%", "(=&", "(=(", "(=)", "(=+", "(=,", "(=-", "(=.", "(=/", "(=:", "(=;", "(=<", "(==", "(=>", "(=?", "(=^", "(=_", "(={", "(=|", "(=}", "(=~", "(> ", "(>#", "(>$", "(>%", "(>&", "(>(", "(>)", "(>+", "(>,", "(>-", "(>.", "(>/", "(>:", "(>;", "(><", "(>=", "(>>", "(>?", "(>^", "(>_", "(>{", "(>|", "(>}", "(>~", "(? ", "(?#", "(?$", "(?%", "(?&", "(?(", "(?)", "(?+", "(?,", "(?-", "(?.", "(?/", "(?:", "(?;", "(?<", "(?=", "(?>", "(??", "(?^", "(?_", "(?{", "(?|", "(?}", "(?~", "(^ ", "(^#", "(^$", "(^%", "(^&", "(^(", "(^)", "(^+", "(^,", "(^-", "(^.", "(^/", "(^:", "(^;", "(^<", "(^=", "(^>", "(^?", "(^^", "(^_", "(^{", "(^|", "(^}", "(^~", "(_ ", "(_#", "(_$", "(_%", "(_&", "(_(", "(_)", "(_+", "(_,", "(_-", "(_.", "(_/", "(_:", "(_;", "(_<", "(_=", "(_>", "(_?", "(_^", "(__", "(_{", "(_|", "(_}", "(_~", "({ ", "({#", "({$", "({%", "({&", "({(", "({)", "({+", "({,", "({-", "({.", "({/", "({:", "({;", "({<", "({=", "({>", "({?", "({^", "({_", "({{", "({|", "({}", "({~", "(| ", "(|#", "(|$", "(|%", "(|&", "(|(", "(|)", "(|+", "(|,", "(|-", "(|.", "(|/", "(|:", "(|;", "(|<", "(|=", "(|>", "(|?", "(|^", "(|_", "(|{", "(||", "(|}", "(|~", "(} ", "(}#", "(}$", "(}%", "(}&", "(}(", "(})", "(}+", "(},", "(}-", "(}.", "(}/", "(}:", "(};", "(}<", "(}=", "(}>", "(}?", "(}^", "(}_", "(}{", "(}|", "(}}", "(}~", "(~ ", "(~#", "(~$", "(~%", "(~&", "(~(", "(~)", "(~+", "(~,", "(~-", "(~.", "(~/", "(~:", "(~;", "(~<", "(~=", "(~>", "(~?", "(~^", "(~_", "(~{", "(~|", "(~}", "(~~", ")  ", ") #", ") $", ") %", ") &", ") (", ") )", ") +", ") ,", ") -", ") .", ") /", ") :", ") ;", ") <", ") =", ") >", ") ?", ") ^", ") _", ") {", ") |", ") }", ") ~", ")# ", ")##", ")#$", ")#%", ")#&", ")#(", ")#)", ")#+", ")#,", ")#-", ")#.", ")#/", ")#:", ")#;", ")#<", ")#=", ")#>", ")#?", ")#^", ")#_", ")#{", ")#|", ")#}", ")#~", ")$ ", ")$#", ")$$", ")$%", ")$&", ")$(", ")$)", ")$+", ")$,", ")$-", ")$.", ")$/", ")$:", ")$;", ")$<", ")$=", ")$>", ")$?", ")$^", ")$_", ")${", ")$|", ")$}", ")$~", ")% ", ")%#", ")%$", ")%%", ")%&", ")%(", ")%)", ")%+", ")%,", ")%-", ")%.", ")%/", ")%:", ")%;", ")%<", ")%=", ")%>", ")%?", ")%^", ")%_", ")%{", ")%|", ")%}", ")%~", ")& ", ")&#", ")&$", ")&%", ")&&", ")&(", ")&)", ")&+", ")&,", ")&-", ")&.", ")&/", ")&:", ")&;", ")&<", ")&=", ")&>", ")&?", ")&^", ")&_", ")&{", ")&|", ")&}", ")&~", ")( ", ")(#", ")($", ")(%", ")(&", ")((", ")()", ")(+", ")(,", ")(-", ")(.", ")(/", ")(:", ")(;", ")(<", ")(=", ")(>", ")(?", ")(^", ")(_", ")({", ")(|", ")(}", ")(~", ")) ", "))#", "))$", "))%", "))&", "))(", ")))", "))+", ")),", "))-", ")).", "))/", ")):", "));", "))<", "))=", "))>", "))?", "))^", "))_", ")){", "))|", "))}", "))~", ")+ ", ")+#", ")+$", ")+%", ")+&", ")+(", ")+)", ")++", ")+,", ")+-", ")+.", ")+/", ")+:", ")+;", ")+<", ")+=", ")+>", ")+?", ")+^", ")+_", ")+{", ")+|", ")+}", ")+~", "), ", "),#", "),$", "),%", "),&", "),(", "),)", "),+", "),,", "),-", "),.", "),/", "),:", "),;", "),<", "),=", "),>", "),?", "),^", "),_", "),{", "),|", "),}", "),~", ")- ", ")-#", ")-$", ")-%", ")-&", ")-(", ")-)", ")-+", ")-,", ")--", ")-.", ")-/", ")-:", ")-;", ")-<", ")-=", ")->", ")-?", ")-^", ")-_", ")-{", ")-|", ")-}", ")-~", "). ", ").#", ").$", ").%", ").&", ").(", ").)", ").+", ").,", ").-", ")..", ")./", ").:", ").;", ").<", ").=", ").>", ").?", ").^", ")._", ").{", ").|", ").}", ").~", ")/ ", ")/#", ")/$", ")/%", ")/&", ")/(", ")/)", ")/+", ")/,", ")/-", ")/.", ")//", ")/:", ")/;", ")/<", ")/=", ")/>", ")/?", ")/^", ")/_", ")/{", ")/|", ")/}", ")/~", "): ", "):#", "):$", "):%", "):&", "):(", "):)", "):+", "):,", "):-", "):.", "):/", ")::", "):;", "):<", "):=", "):>", "):?", "):^", "):_", "):{", "):|", "):}", "):~", "); ", ");#", ");$", ");%", ");&", ");(", ");)", ");+", ");,", ");-", ");.", ");/", ");:", ");;", ");<", ");=", ");>", ");?", ");^", ");_", ");{", ");|", ");}", ");~", ")< ", ")<#", ")<$", ")<%", ")<&", ")<(", ")<)", ")<+", ")<,", ")<-", ")<.", ")</", ")<:", ")<;", ")<<", ")<=", ")<>", ")<?", ")<^", ")<_", ")<{", ")<|", ")<}", ")<~", ")= ", ")=#", ")=$", ")=%", ")=&", ")=(", ")=)", ")=+", ")=,", ")=-", ")=.", ")=/", ")=:", ")=;", ")=<", ")==", ")=>", ")=?", ")=^", ")=_", ")={", ")=|", ")=}", ")=~", ")> ", ")>#", ")>$", ")>%", ")>&", ")>(", ")>)", ")>+", ")>,", ")>-", ")>.", ")>/", ")>:", ")>;", ")><", ")>=", ")>>", ")>?", ")>^", ")>_", ")>{", ")>|", ")>}", ")>~", ")? ", ")?#", ")?$", ")?%", ")?&", ")?(", ")?)", ")?+", ")?,", ")?-", ")?.", ")?/", ")?:", ")?;", ")?<", ")?=", ")?>", ")??", ")?^", ")?_", ")?{", ")?|", ")?}", ")?~", ")^ ", ")^#", ")^$", ")^%", ")^&", ")^(", ")^)", ")^+", ")^,", ")^-", ")^.", ")^/", ")^:", ")^;", ")^<", ")^=", ")^>", ")^?", ")^^", ")^_", ")^{", ")^|", ")^}", ")^~", ")_ ", ")_#", ")_$", ")_%", ")_&", ")_(", ")_)", ")_+", ")_,", ")_-", ")_.", ")_/", ")_:", ")_;", ")_<", ")_=", ")_>", ")_?", ")_^", ")__", ")_{", ")_|", ")_}", ")_~", "){ ", "){#", "){$", "){%", "){&", "){(", "){)", "){+", "){,", "){-", "){.", "){/", "){:", "){;", "){<", "){=", "){>", "){?", "){^", "){_", "){{", "){|", "){}", "){~", ")| ", ")|#", ")|$", ")|%", ")|&", ")|(", ")|)", ")|+", ")|,", ")|-", ")|.", ")|/", ")|:", ")|;", ")|<", ")|=", ")|>", ")|?", ")|^", ")|_", ")|{", ")||", ")|}", ")|~", ")} ", ")}#", ")}$", ")}%", ")}&", ")}(", ")})", ")}+", ")},", ")}-", ")}.", ")}/", ")}:", ")};", ")}<", ")}=", ")}>", ")}?", ")}^", ")}_", ")}{", ")}|", ")}}", ")}~", ")~ ", ")~#", ")~$", ")~%", ")~&", ")~(", ")~)", ")~+", ")~,", ")~-", ")~.", ")~/", ")~:", ")~;", ")~<", ")~=", ")~>", ")~?", ")~^", ")~_", ")~{", ")~|", ")~}", ")~~", "+  ", "+ #", "+ $", "+ &", "+ (", "+ )", "+ ;", "+ <", "+ >", "+ ?", "+ |", "+#$", "+#&", "+#(", "+#)", "+#;", "+#<", "+#>", "+#|", "+$#", "+$$", "+$&", "+$(", "+$)", "+$-", "+$;", "+$<", "+$>", "+$?", "+$_", "+${", "+$|", "+%$", "+%&", "+%(", "+%)", "+%;", "+%<", "+%>", "+%|", "+& ", "+&#", "+&$", "+&%", "+&&", "+&(", "+&)", "+&+", "+&,", "+&-", "+&.", "+&/", "+&:", "+&;", "+&<", "+&=", "+&>", "+&?", "+&^", "+&_", "+&{", "+&|", "+&}", "+&~", "+( ", "+(#", "+($", "+(%", "+(&", "+((", "+()", "+(+", "+(,", "+(-", "+(.", "+(/", "+(:", "+(;", "+(<", "+(=", "+(>", "+(?", "+(^", "+(_", "+({", "+(|", "+(}", "+(~", "+) ", "+)#", "+)$", "+)%", "+)&", "+)(", "+))", "+)+", "+),", "+)-", "+).", "+)/", "+):", "+);", "+)<", "+)=", "+)>", "+)?", "+)^", "+)_", "+){", "+)|", "+)}", "+)~", "++$", "++&", "++(", "++)", "++;", "++<", "++>", "++|", "+,$", "+,&", "+,(", "+,)", "+,;", "+,<", "+,>", "+,|", "+-$", "+-&", "+-(", "+-)", "+-;", "+-<", "+->", "+-|", "+.$", "+.&", "+.(", "+.)", "+.;", "+.<", "+.>", "+.|", "+/$", "+/&", "+/(", "+/)", "+/;", "+/<", "+/>", "+/|", "+:$", "+:&", "+:(", "+:)", "+:;", "+:<", "+:>", "+:|", "+:~", "+; ", "+;#", "+;$", "+;%", "+;&", "+;(", "+;)", "+;+", "+;,", "+;-", "+;.", "+;/", "+;:", "+;;", "+;<", "+;=", "+;>", "+;?", "+;^", "+;_", "+;{", "+;|", "+;}", "+;~", "+< ", "+<#", "+<$", "+<%", "+<&", "+<(", "+<)", "+<+", "+<,", "+<-", "+<.", "+</", "+<:", "+<;", "+<<", "+<=", "+<>", "+<?", "+<^", "+<_", "+<{", "+<|", "+<}", "+<~", "+=$", "+=&", "+=(", "+=)", "+=;", "+=<", "+=>", "+=|", "+> ", "+>#", "+>$", "+>%", "+>&", "+>(", "+>)", "+>+", "+>,", "+>-", "+>.", "+>/", "+>:", "+>;", "+><", "+>=", "+>>", "+>?", "+>^", "+>_", "+>{", "+>|", "+>}", "+>~", "+?$", "+?&", "+?(", "+?)", "+?;", "+?<", "+?>", "+?|", "+^$", "+^&", "+^(", "+^)", "+^;", "+^<", "+^>", "+^|", "+_$", "+_&", "+_(", "+_)", "+_;", "+_<", "+_>", "+_|", "+{$", "+{&", "+{(", "+{)", "+{;", "+{<", "+{>", "+{|", "+| ", "+|#", "+|$", "+|%", "+|&", "+|(", "+|)", "+|+", "+|,", "+|-", "+|.", "+|/", "+|:", "+|;", "+|<", "+|=", "+|>", "+|?", "+|^", "+|_", "+|{", "+||", "+|}", "+|~", "+} ", "+}$", "+}&", "+}(", "+})", "+};", "+}<", "+}>", "+}|", "+~$", "+~&", "+~(", "+~)", "+~;", "+~<", "+~>", "+~|", ",  ", ", #", ", $", ", &", ", (", ", )", ", ;", ", <", ", >", ", ?", ", |", ",#$", ",#&", ",#(", ",#)", ",#;", ",#<", ",#>", ",#|", ",$#", ",$$", ",$&", ",$(", ",$)", ",$-", ",$;", ",$<", ",$>", ",$?", ",$_", ",${", ",$|", ",%$", ",%&", ",%(", ",%)", ",%;", ",%<", ",%>", ",%|", ",& ", ",&#", ",&$", ",&%", ",&&", ",&(", ",&)", ",&+", ",&,", ",&-", ",&.", ",&/", ",&:", ",&;", ",&<", ",&=", ",&>", ",&?", ",&^", ",&_", ",&{", ",&|", ",&}", ",&~", ",( ", ",(#", ",($", ",(%", ",(&", ",((", ",()", ",(+", ",(,", ",(-", ",(.", ",(/", ",(:", ",(;", ",(<", ",(=", ",(>", ",(?", ",(^", ",(_", ",({", ",(|", ",(}", ",(~", ",) ", ",)#", ",)$", ",)%", ",)&", ",)(", ",))", ",)+", ",),", ",)-", ",).", ",)/", ",):", ",);", ",)<", ",)=", ",)>", ",)?", ",)^", ",)_", ",){", ",)|", ",)}", ",)~", ",+$", ",+&", ",+(", ",+)", ",+;", ",+<", ",+>", ",+|", ",,$", ",,&", ",,(", ",,)", ",,;", ",,<", ",,>", ",,|", ",-$", ",-&", ",-(", ",-)", ",-;", ",-<", ",->", ",-|", ",.$", ",.&", ",.(", ",.)", ",.;", ",.<", ",.>", ",.|", ",/$", ",/&", ",/(", ",/)", ",/;", ",/<", ",/>", ",/|", ",:$", ",:&", ",:(", ",:)", ",:;", ",:<", ",:>", ",:|", ",:~", ",; ", ",;#", ",;$", ",;%", ",;&", ",;(", ",;)", ",;+", ",;,", ",;-", ",;.", ",;/", ",;:", ",;;", ",;<", ",;=", ",;>", ",;?", ",;^", ",;_", ",;{", ",;|", ",;}", ",;~", ",< ", ",<#", ",<$", ",<%", ",<&", ",<(", ",<)", ",<+", ",<,", ",<-", ",<.", ",</", ",<:", ",<;", ",<<", ",<=", ",<>", ",<?", ",<^", ",<_", ",<{", ",<|", ",<}", ",<~", ",=$", ",=&", ",=(", ",=)", ",=;", ",=<", ",=>", ",=|", ",> ", ",>#", ",>$", ",>%", ",>&", ",>(", ",>)", ",>+", ",>,", ",>-", ",>.", ",>/", ",>:", ",>;", ",><", ",>=", ",>>", ",>?", ",>^", ",>_", ",>{", ",>|", ",>}", ",>~", ",?$", ",?&", ",?(", ",?)", ",?;", ",?<", ",?>", ",?|", ",^$", ",^&", ",^(", ",^)", ",^;", ",^<", ",^>", ",^|", ",_$", ",_&", ",_(", ",_)", ",_;", ",_<", ",_>", ",_|", ",{$", ",{&", ",{(", ",{)", ",{;", ",{<", ",{>", ",{|", ",| ", ",|#", ",|$", ",|%", ",|&", ",|(", ",|)", ",|+", ",|,", ",|-", ",|.", ",|/", ",|:", ",|;", ",|<", ",|=", ",|>", ",|?", ",|^", ",|_", ",|{", ",||", ",|}", ",|~", ",} ", ",}$", ",}&", ",}(", ",})", ",};", ",}<", ",}>", ",}|", ",~$", ",~&", ",~(", ",~)", ",~;", ",~<", ",~>", ",~|", "-  ", "- #", "- $", "- &", "- (", "- )", "- ;", "- <", "- >", "- ?", "- |", "-#$", "-#&", "-#(", "-#)", "-#;", "-#<", "-#>", "-#|", "-$#", "-$$", "-$&", "-$(", "-$)", "-$-", "-$;", "-$<", "-$>", "-$?", "-$_", "-${", "-$|", "-%$", "-%&", "-%(", "-%)", "-%;", "-%<", "-%>", "-%|", "-& ", "-&#", "-&$", "-&%", "-&&", "-&(", "-&)", "-&+", "-&,", "-&-", "-&.", "-&/", "-&:", "-&;", "-&<", "-&=", "-&>", "-&?", "-&^", "-&_", "-&{", "-&|", "-&}", "-&~", "-( ", "-(#", "-($", "-(%", "-(&", "-((", "-()", "-(+", "-(,", "-(-", "-(.", "-(/", "-(:", "-(;", "-(<", "-(=", "-(>", "-(?", "-(^", "-(_", "-({", "-(|", "-(}", "-(~", "-) ", "-)#", "-)$", "-)%", "-)&", "-)(", "-))", "-)+", "-),", "-)-", "-).", "-)/", "-):", "-);", "-)<", "-)=", "-)>", "-)?", "-)^", "-)_", "-){", "-)|", "-)}", "-)~", "-+$", "-+&", "-+(", "-+)", "-+;", "-+<", "-+>", "-+|", "-,$", "-,&", "-,(", "-,)", "-,;", "-,<", "-,>", "-,|", "--$", "--&", "--(", "--)", "--;", "--<", "-->", "--|", "-.$", "-.&", "-.(", "-.)", "-.;", "-.<", "-.>", "-.|", "-/$", "-/&", "-/(", "-/)", "-/;", "-/<", "-/>", "-/|", "-:$", "-:&", "-:(", "-:)", "-:;", "-:<", "-:>", "-:|", "-:~", "-; ", "-;#", "-;$", "-;%", "-;&", "-;(", "-;)", "-;+", "-;,", "-;-", "-;.", "-;/", "-;:", "-;;", "-;<", "-;=", "-;>", "-;?", "-;^", "-;_", "-;{", "-;|", "-;}", "-;~", "-< ", "-<#", "-<$", "-<%", "-<&", "-<(", "-<)", "-<+", "-<,", "-<-", "-<.", "-</", "-<:", "-<;", "-<<", "-<=", "-<>", "-<?", "-<^", "-<_", "-<{", "-<|", "-<}", "-<~", "-=$", "-=&", "-=(", "-=)", "-=;", "-=<", "-=>", "-=|", "-> ", "->#", "->$", "->%", "->&", "->(", "->)", "->+", "->,", "->-", "->.", "->/", "->:", "->;", "-><", "->=", "->>", "->?", "->^", "->_", "->{", "->|", "->}", "->~", "-?$", "-?&", "-?(", "-?)", "-?;", "-?<", "-?>", "-?|", "-^$", "-^&", "-^(", "-^)", "-^;", "-^<", "-^>", "-^|", "-_$", "-_&", "-_(", "-_)", "-_;", "-_<", "-_>", "-_|", "-{$", "-{&", "-{(", "-{)", "-{;", "-{<", "-{>", "-{|", "-| ", "-|#", "-|$", "-|%", "-|&", "-|(", "-|)", "-|+", "-|,", "-|-", "-|.", "-|/", "-|:", "-|;", "-|<", "-|=", "-|>", "-|?", "-|^", "-|_", "-|{", "-||", "-|}", "-|~", "-} ", "-}$", "-}&", "-}(", "-})", "-};", "-}<", "-}>", "-}|", "-~$", "-~&", "-~(", "-~)", "-~;", "-~<", "-~>", "-~|", ".  ", ". #", ". $", ". &", ". (", ". )", ". ;", ". <", ". >", ". ?", ". |", ".#$", ".#&", ".#(", ".#)", ".#;", ".#<", ".#>", ".#|", ".$#", ".$$", ".$&", ".$(", ".$)", ".$-", ".$;", ".$<", ".$>", ".$?", ".$_", ".${", ".$|", ".%$", ".%&", ".%(", ".%)", ".%;", ".%<", ".%>", ".%|", ".& ", ".&#", ".&$", ".&%", ".&&", ".&(", ".&)", ".&+", ".&,", ".&-", ".&.", ".&/", ".&:", ".&;", ".&<", ".&=", ".&>", ".&?", ".&^", ".&_", ".&{", ".&|", ".&}", ".&~", ".( ", ".(#", ".($", ".(%", ".(&", ".((", ".()", ".(+", ".(,", ".(-", ".(.", ".(/", ".(:", ".(;", ".(<", ".(=", ".(>", ".(?", ".(^", ".(_", ".({", ".(|", ".(}", ".(~", ".) ", ".)#", ".)$", ".)%", ".)&", ".)(", ".))", ".)+", ".),", ".)-", ".).", ".)/", ".):", ".);", ".)<", ".)=", ".)>", ".)?", ".)^", ".)_", ".){", ".)|", ".)}", ".)~", ".+$", ".+&", ".+(", ".+)", ".+;", ".+<", ".+>", ".+|", ".,$", ".,&", ".,(", ".,)", ".,;", ".,<", ".,>", ".,|", ".-$", ".-&", ".-(", ".-)", ".-;", ".-<", ".->", ".-|", "..$", "..&", "..(", "..)", "..;", "..<", "..>", "..|", "./$", "./&", "./(", "./)", "./;", "./<", "./>", "./|", ".:$", ".:&", ".:(", ".:)", ".:;", ".:<", ".:>", ".:|", ".:~", ".; ", ".;#", ".;$", ".;%", ".;&", ".;(", ".;)", ".;+", ".;,", ".;-", ".;.", ".;/", ".;:", ".;;", ".;<", ".;=", ".;>", ".;?", ".;^", ".;_", ".;{", ".;|", ".;}", ".;~", ".< ", ".<#", ".<$", ".<%", ".<&", ".<(", ".<)", ".<+", ".<,", ".<-", ".<.", ".</", ".<:", ".<;", ".<<", ".<=", ".<>", ".<?", ".<^", ".<_", ".<{", ".<|", ".<}", ".<~", ".=$", ".=&", ".=(", ".=)", ".=;", ".=<", ".=>", ".=|", ".> ", ".>#", ".>$", ".>%", ".>&", ".>(", ".>)", ".>+", ".>,", ".>-", ".>.", ".>/", ".>:", ".>;", ".><", ".>=", ".>>", ".>?", ".>^", ".>_", ".>{", ".>|", ".>}", ".>~", ".?$", ".?&", ".?(", ".?)", ".?;", ".?<", ".?>", ".?|", ".^$", ".^&", ".^(", ".^)", ".^;", ".^<", ".^>", ".^|", "._$", "._&", "._(", "._)", "._;", "._<", "._>", "._|", ".{$", ".{&", ".{(", ".{)", ".{;", ".{<", ".{>", ".{|", ".| ", ".|#", ".|$", ".|%", ".|&", ".|(", ".|)", ".|+", ".|,", ".|-", ".|.", ".|/", ".|:", ".|;", ".|<", ".|=", ".|>", ".|?", ".|^", ".|_", ".|{", ".||", ".|}", ".|~", ".} ", ".}$", ".}&", ".}(", ".})", ".};", ".}<", ".}>", ".}|", ".~$", ".~&", ".~(", ".~)", ".~;", ".~<", ".~>", ".~|", "/  ", "/ #", "/ $", "/ &", "/ (", "/ )", "/ ;", "/ <", "/ >", "/ ?", "/ |", "/#$", "/#&", "/#(", "/#)", "/#;", "/#<", "/#>", "/#|", "/$#", "/$$", "/$&", "/$(", "/$)", "/$-", "/$;", "/$<", "/$>", "/$?", "/$_", "/${", "/$|", "/%$", "/%&", "/%(", "/%)", "/%;", "/%<", "/%>", "/%|", "/& ", "/&#", "/&$", "/&%", "/&&", "/&(", "/&)", "/&+", "/&,", "/&-", "/&.", "/&/", "/&:", "/&;", "/&<", "/&=", "/&>", "/&?", "/&^", "/&_", "/&{", "/&|", "/&}", "/&~", "/( ", "/(#", "/($", "/(%", "/(&", "/((", "/()", "/(+", "/(,", "/(-", "/(.", "/(/", "/(:", "/(;", "/(<", "/(=", "/(>", "/(?", "/(^", "/(_", "/({", "/(|", "/(}", "/(~", "/) ", "/)#", "/)$", "/)%", "/)&", "/)(", "/))", "/)+", "/),", "/)-", "/).", "/)/", "/):", "/);", "/)<", "/)=", "/)>", "/)?", "/)^", "/)_", "/){", "/)|", "/)}", "/)~", "/+$", "/+&", "/+(", "/+)", "/+;", "/+<", "/+>", "/+|", "/,$", "/,&", "/,(", "/,)", "/,;", "/,<", "/,>", "/,|", "/-$", "/-&", "/-(", "/-)", "/-;", "/-<", "/->", "/-|", "/.$", "/.&", "/.(", "/.)", "/.;", "/.<", "/.>", "/.|", "//$", "//&", "//(", "//)", "//;", "//<", "//>", "//|", "/:$", "/:&", "/:(", "/:)", "/:;", "/:<", "/:>", "/:|", "/:~", "/; ", "/;#", "/;$", "/;%", "/;&", "/;(", "/;)", "/;+", "/;,", "/;-", "/;.", "/;/", "/;:", "/;;", "/;<", "/;=", "/;>", "/;?", "/;^", "/;_", "/;{", "/;|", "/;}", "/;~", "/< ", "/<#", "/<$", "/<%", "/<&", "/<(", "/<)", "/<+", "/<,", "/<-", "/<.", "/</", "/<:", "/<;", "/<<", "/<=", "/<>", "/<?", "/<^", "/<_", "/<{", "/<|", "/<}", "/<~", "/=$", "/=&", "/=(", "/=)", "/=;", "/=<", "/=>", "/=|", "/> ", "/>#", "/>$", "/>%", "/>&", "/>(", "/>)", "/>+", "/>,", "/>-", "/>.", "/>/", "/>:", "/>;", "/><", "/>=", "/>>", "/>?", "/>^", "/>_", "/>{", "/>|", "/>}", "/>~", "/?$", "/?&", "/?(", "/?)", "/?;", "/?<", "/?>", "/?|", "/^$", "/^&", "/^(", "/^)", "/^;", "/^<", "/^>", "/^|", "/_$", "/_&", "/_(", "/_)", "/_;", "/_<", "/_>", "/_|", "/{$", "/{&", "/{(", "/{)", "/{;", "/{<", "/{>", "/{|", "/| ", "/|#", "/|$", "/|%", "/|&", "/|(", "/|)", "/|+", "/|,", "/|-", "/|.", "/|/", "/|:", "/|;", "/|<", "/|=", "/|>", "/|?", "/|^", "/|_", "/|{", "/||", "/|}", "/|~", "/} ", "/}$", "/}&", "/}(", "/})", "/};", "/}<", "/}>", "/}|", "/~$", "/~&", "/~(", "/~)", "/~;", "/~<", "/~>", "/~|", ":  ", ": #", ": $", ": &", ": (", ": )", ": ;", ": <", ": >", ": ?", ": |", ":#$", ":#&", ":#(", ":#)", ":#;", ":#<", ":#>", ":#|", ":$#", ":$$", ":$&", ":$(", ":$)", ":$-", ":$;", ":$<", ":$>", ":$?", ":$_", ":${", ":$|", ":%$", ":%&", ":%(", ":%)", ":%;", ":%<", ":%>", ":%|", ":& ", ":&#", ":&$", ":&%", ":&&", ":&(", ":&)", ":&+", ":&,", ":&-", ":&.", ":&/", ":&:", ":&;", ":&<", ":&=", ":&>", ":&?", ":&^", ":&_", ":&{", ":&|", ":&}", ":&~", ":( ", ":(#", ":($", ":(%", ":(&", ":((", ":()", ":(+", ":(,", ":(-", ":(.", ":(/", ":(:", ":(;", ":(<", ":(=", ":(>", ":(?", ":(^", ":(_", ":({", ":(|", ":(}", ":(~", ":) ", ":)#", ":)$", ":)%", ":)&", ":)(", ":))", ":)+", ":),", ":)-", ":).", ":)/", ":):", ":);", ":)<", ":)=", ":)>", ":)?", ":)^", ":)_", ":){", ":)|", ":)}", ":)~", ":+$", ":+&", ":+(", ":+)", ":+;", ":+<", ":+>", ":+|", ":,$", ":,&", ":,(", ":,)", ":,;", ":,<", ":,>", ":,|", ":-$", ":-&", ":-(", ":-)", ":-;", ":-<", ":->", ":-|", ":.$", ":.&", ":.(", ":.)", ":.;", ":.<", ":.>", ":.|", ":/$", ":/&", ":/(", ":/)", ":/;", ":/<", ":/>", ":/|", "::$", "::&", "::(", "::)", "::;", "::<", "::>", "::|", "::~", ":; ", ":;#", ":;$", ":;%", ":;&", ":;(", ":;)", ":;+", ":;,", ":;-", ":;.", ":;/", ":;:", ":;;", ":;<", ":;=", ":;>", ":;?", ":;^", ":;_", ":;{", ":;|", ":;}", ":;~", ":< ", ":<#", ":<$", ":<%", ":<&", ":<(", ":<)", ":<+", ":<,", ":<-", ":<.", ":</", ":<:", ":<;", ":<<", ":<=", ":<>", ":<?", ":<^", ":<_", ":<{", ":<|", ":<}", ":<~", ":=$", ":=&", ":=(", ":=)", ":=;", ":=<", ":=>", ":=|", ":> ", ":>#", ":>$", ":>%", ":>&", ":>(", ":>)", ":>+", ":>,", ":>-", ":>.", ":>/", ":>:", ":>;", ":><", ":>=", ":>>", ":>?", ":>^", ":>_", ":>{", ":>|", ":>}", ":>~", ":?$", ":?&", ":?(", ":?)", ":?;", ":?<", ":?>", ":?|", ":^$", ":^&", ":^(", ":^)", ":^;", ":^<", ":^>", ":^|", ":_$", ":_&", ":_(", ":_)", ":_;", ":_<", ":_>", ":_|", ":{$", ":{&", ":{(", ":{)", ":{;", ":{<", ":{>", ":{|", ":| ", ":|#", ":|$", ":|%", ":|&", ":|(", ":|)", ":|+", ":|,", ":|-", ":|.", ":|/", ":|:", ":|;", ":|<", ":|=", ":|>", ":|?", ":|^", ":|_", ":|{", ":||", ":|}", ":|~", ":} ", ":}$", ":}&", ":}(", ":})", ":};", ":}<", ":}>", ":}|", ":~$", ":~&", ":~(", ":~)", ":~+", ":~-", ":~/", ":~:", ":~;", ":~<", ":~>", ":~|", ";  ", "; #", "; $", "; %", "; &", "; (", "; )", "; +", "; ,", "; -", "; .", "; /", "; :", "; ;", "; <", "; =", "; >", "; ?", "; ^", "; _", "; {", "; |", "; }", "; ~", ";# ", ";##", ";#$", ";#%", ";#&", ";#(", ";#)", ";#+", ";#,", ";#-", ";#.", ";#/", ";#:", ";#;", ";#<", ";#=", ";#>", ";#?", ";#^", ";#_", ";#{", ";#|", ";#}", ";#~", ";$ ", ";$#", ";$$", ";$%", ";$&", ";$(", ";$)", ";$+", ";$,", ";$-", ";$.", ";$/", ";$:", ";$;", ";$<", ";$=", ";$>", ";$?", ";$^", ";$_", ";${", ";$|", ";$}", ";$~", ";% ", ";%#", ";%$", ";%%", ";%&", ";%(", ";%)", ";%+", ";%,", ";%-", ";%.", ";%/", ";%:", ";%;", ";%<", ";%=", ";%>", ";%?", ";%^", ";%_", ";%{", ";%|", ";%}", ";%~", ";& ", ";&#", ";&$", ";&%", ";&&", ";&(", ";&)", ";&+", ";&,", ";&-", ";&.", ";&/", ";&:", ";&;", ";&<", ";&=", ";&>", ";&?", ";&^", ";&_", ";&{", ";&|", ";&}", ";&~", ";( ", ";(#", ";($", ";(%", ";(&", ";((", ";()", ";(+", ";(,", ";(-", ";(.", ";(/", ";(:", ";(;", ";(<", ";(=", ";(>", ";(?", ";(^", ";(_", ";({", ";(|", ";(}", ";(~", ";) ", ";)#", ";)$", ";)%", ";)&", ";)(", ";))", ";)+", ";),", ";)-", ";).", ";)/", ";):", ";);", ";)<", ";)=", ";)>", ";)?", ";)^", ";)_", ";){", ";)|", ";)}", ";)~", ";+ ", ";+#", ";+$", ";+%", ";+&", ";+(", ";+)", ";++", ";+,", ";+-", ";+.", ";+/", ";+:", ";+;", ";+<", ";+=", ";+>", ";+?", ";+^", ";+_", ";+{", ";+|", ";+}", ";+~", ";, ", ";,#", ";,$", ";,%", ";,&", ";,(", ";,)", ";,+", ";,,", ";,-", ";,.", ";,/", ";,:", ";,;", ";,<", ";,=", ";,>", ";,?", ";,^", ";,_", ";,{", ";,|", ";,}", ";,~", ";- ", ";-#", ";-$", ";-%", ";-&", ";-(", ";-)", ";-+", ";-,", ";--", ";-.", ";-/", ";-:", ";-;", ";-<", ";-=", ";->", ";-?", ";-^", ";-_", ";-{", ";-|", ";-}", ";-~", ";. ", ";.#", ";.$", ";.%", ";.&", ";.(", ";.)", ";.+", ";.,", ";.-", ";..", ";./", ";.:", ";.;", ";.<", ";.=", ";.>", ";.?", ";.^", ";._", ";.{", ";.|", ";.}", ";.~", ";/ ", ";/#", ";/$", ";/%", ";/&", ";/(", ";/)", ";/+", ";/,", ";/-", ";/.", ";//", ";/:", ";/;", ";/<", ";/=", ";/>", ";/?", ";/^", ";/_", ";/{", ";/|", ";/}", ";/~", ";: ", ";:#", ";:$", ";:%", ";:&", ";:(", ";:)", ";:+", ";:,", ";:-", ";:.", ";:/", ";::", ";:;", ";:<", ";:=", ";:>", ";:?", ";:^", ";:_", ";:{", ";:|", ";:}", ";:~", ";; ", ";;#", ";;$", ";;%", ";;&", ";;(", ";;)", ";;+", ";;,", ";;-", ";;.", ";;/", ";;:", ";;;", ";;<", ";;=", ";;>", ";;?", ";;^", ";;_", ";;{", ";;|", ";;}", ";;~", ";< ", ";<#", ";<$", ";<%", ";<&", ";<(", ";<)", ";<+", ";<,", ";<-", ";<.", ";</", ";<:", ";<;", ";<<", ";<=", ";<>", ";<?", ";<^", ";<_", ";<{", ";<|", ";<}", ";<~", ";= ", ";=#", ";=$", ";=%", ";=&", ";=(", ";=)", ";=+", ";=,", ";=-", ";=.", ";=/", ";=:", ";=;", ";=<", ";==", ";=>", ";=?", ";=^", ";=_", ";={", ";=|", ";=}", ";=~", ";> ", ";>#", ";>$", ";>%", ";>&", ";>(", ";>)", ";>+", ";>,", ";>-", ";>.", ";>/", ";>:", ";>;", ";><", ";>=", ";>>", ";>?", ";>^", ";>_", ";>{", ";>|", ";>}", ";>~", ";? ", ";?#", ";?$", ";?%", ";?&", ";?(", ";?)", ";?+", ";?,", ";?-", ";?.", ";?/", ";?:", ";?;", ";?<", ";?=", ";?>", ";??", ";?^", ";?_", ";?{", ";?|", ";?}", ";?~", ";^ ", ";^#", ";^$", ";^%", ";^&", ";^(", ";^)", ";^+", ";^,", ";^-", ";^.", ";^/", ";^:", ";^;", ";^<", ";^=", ";^>", ";^?", ";^^", ";^_", ";^{", ";^|", ";^}", ";^~", ";_ ", ";_#", ";_$", ";_%", ";_&", ";_(", ";_)", ";_+", ";_,", ";_-", ";_.", ";_/", ";_:", ";_;", ";_<", ";_=", ";_>", ";_?", ";_^", ";__", ";_{", ";_|", ";_}", ";_~", ";{ ", ";{#", ";{$", ";{%", ";{&", ";{(", ";{)", ";{+", ";{,", ";{-", ";{.", ";{/", ";{:", ";{;", ";{<", ";{=", ";{>", ";{?", ";{^", ";{_", ";{{", ";{|", ";{}", ";{~", ";| ", ";|#", ";|$", ";|%", ";|&", ";|(", ";|)", ";|+", ";|,", ";|-", ";|.", ";|/", ";|:", ";|;", ";|<", ";|=", ";|>", ";|?", ";|^", ";|_", ";|{", ";||", ";|}", ";|~", ";} ", ";}#", ";}$", ";}%", ";}&", ";}(", ";})", ";}+", ";},", ";}-", ";}.", ";}/", ";}:", ";};", ";}<", ";}=", ";}>", ";}?", ";}^", ";}_", ";}{", ";}|", ";}}", ";}~", ";~ ", ";~#", ";~$", ";~%", ";~&", ";~(", ";~)", ";~+", ";~,", ";~-", ";~.", ";~/", ";~:", ";~;", ";~<", ";~=", ";~>", ";~?", ";~^", ";~_", ";~{", ";~|", ";~}", ";~~", "<  ", "< #", "< $", "< %", "< &", "< (", "< )", "< +", "< ,", "< -", "< .", "< /", "< :", "< ;", "< <", "< =", "< >", "< ?", "< ^", "< _", "< {", "< |", "< }", "< ~", "<# ", "<##", "<#$", "<#%", "<#&", "<#(", "<#)", "<#+", "<#,", "<#-", "<#.", "<#/", "<#:", "<#;", "<#<", "<#=", "<#>", "<#?", "<#^", "<#_", "<#{", "<#|", "<#}", "<#~", "<$ ", "<$#", "<$$", "<$%", "<$&", "<$(", "<$)", "<$+", "<$,", "<$-", "<$.", "<$/", "<$:", "<$;", "<$<", "<$=", "<$>", "<$?", "<$^", "<$_", "<${", "<$|", "<$}", "<$~", "<% ", "<%#", "<%$", "<%%", "<%&", "<%(", "<%)", "<%+", "<%,", "<%-", "<%.", "<%/", "<%:", "<%;", "<%<", "<%=", "<%>", "<%?", "<%^", "<%_", "<%{", "<%|", "<%}", "<%~", "<& ", "<&#", "<&$", "<&%", "<&&", "<&(", "<&)", "<&+", "<&,", "<&-", "<&.", "<&/", "<&:", "<&;", "<&<", "<&=", "<&>", "<&?", "<&^", "<&_", "<&{", "<&|", "<&}", "<&~", "<( ", "<(#", "<($", "<(%", "<(&", "<((", "<()", "<(+", "<(,", "<(-", "<(.", "<(/", "<(:", "<(;", "<(<", "<(=", "<(>", "<(?", "<(^", "<(_", "<({", "<(|", "<(}", "<(~", "<) ", "<)#", "<)$", "<)%", "<)&", "<)(", "<))", "<)+", "<),", "<)-", "<).", "<)/", "<):", "<);", "<)<", "<)=", "<)>", "<)?", "<)^", "<)_", "<){", "<)|", "<)}", "<)~", "<+ ", "<+#", "<+$", "<+%", "<+&", "<+(", "<+)", "<++", "<+,", "<+-", "<+.", "<+/", "<+:", "<+;", "<+<", "<+=", "<+>", "<+?", "<+^", "<+_", "<+{", "<+|", "<+}", "<+~", "<, ", "<,#", "<,$", "<,%", "<,&", "<,(", "<,)", "<,+", "<,,", "<,-", "<,.", "<,/", "<,:", "<,;", "<,<", "<,=", "<,>", "<,?", "<,^", "<,_", "<,{", "<,|", "<,}", "<,~", "<- ", "<-#", "<-$", "<-%", "<-&", "<-(", "<-)", "<-+", "<-,", "<--", "<-.", "<-/", "<-:", "<-;", "<-<", "<-=", "<->", "<-?", "<-^", "<-_", "<-{", "<-|", "<-}", "<-~", "<. ", "<.#", "<.$", "<.%", "<.&", "<.(", "<.)", "<.+", "<.,", "<.-", "<..", "<./", "<.:", "<.;", "<.<", "<.=", "<.>", "<.?", "<.^", "<._", "<.{", "<.|", "<.}", "<.~", "</ ", "</#", "</$", "</%", "</&", "</(", "</)", "</+", "</,", "</-", "</.", "<//", "</:", "</;", "</<", "</=", "</>", "</?", "</^", "</_", "</{", "</|", "</}", "</~", "<: ", "<:#", "<:$", "<:%", "<:&", "<:(", "<:)", "<:+", "<:,", "<:-", "<:.", "<:/", "<::", "<:;", "<:<", "<:=", "<:>", "<:?", "<:^", "<:_", "<:{", "<:|", "<:}", "<:~", "<; ", "<;#", "<;$", "<;%", "<;&", "<;(", "<;)", "<;+", "<;,", "<;-", "<;.", "<;/", "<;:", "<;;", "<;<", "<;=", "<;>", "<;?", "<;^", "<;_", "<;{", "<;|", "<;}", "<;~", "<< ", "<<#", "<<$", "<<%", "<<&", "<<(", "<<)", "<<+", "<<,", "<<-", "<<.", "<</", "<<:", "<<;", "<<<", "<<=", "<<>", "<<?", "<<^", "<<_", "<<{", "<<|", "<<}", "<<~", "<= ", "<=#", "<=$", "<=%", "<=&", "<=(", "<=)", "<=+", "<=,", "<=-", "<=.", "<=/", "<=:", "<=;", "<=<", "<==", "<=>", "<=?", "<=^", "<=_", "<={", "<=|", "<=}", "<=~", "<> ", "<>#", "<>$", "<>%", "<>&", "<>(", "<>)", "<>+", "<>,", "<>-", "<>.", "<>/", "<>:", "<>;", "<><", "<>=", "<>>", "<>?", "<>^", "<>_", "<>{", "<>|", "<>}", "<>~", "<? ", "<?#", "<?$", "<?%", "<?&", "<?(", "<?)", "<?+", "<?,", "<?-", "<?.", "<?/", "<?:", "<?;", "<?<", "<?=", "<?>", "<??", "<?^", "<?_", "<?{", "<?|", "<?}", "<?~", "<^ ", "<^#", "<^$", "<^%", "<^&", "<^(", "<^)", "<^+", "<^,", "<^-", "<^.", "<^/", "<^:", "<^;", "<^<", "<^=", "<^>", "<^?", "<^^", "<^_", "<^{", "<^|", "<^}", "<^~", "<_ ", "<_#", "<_$", "<_%", "<_&", "<_(", "<_)", "<_+", "<_,", "<_-", "<_.", "<_/", "<_:", "<_;", "<_<", "<_=", "<_>", "<_?", "<_^", "<__", "<_{", "<_|", "<_}", "<_~", "<{ ", "<{#", "<{$", "<{%", "<{&", "<{(", "<{)", "<{+", "<{,", "<{-", "<{.", "<{/", "<{:", "<{;", "<{<", "<{=", "<{>", "<{?", "<{^", "<{_", "<{{", "<{|", "<{}", "<{~", "<| ", "<|#", "<|$", "<|%", "<|&", "<|(", "<|)", "<|+", "<|,", "<|-", "<|.", "<|/", "<|:", "<|;", "<|<", "<|=", "<|>", "<|?", "<|^", "<|_", "<|{", "<||", "<|}", "<|~", "<} ", "<}#", "<}$", "<}%", "<}&", "<}(", "<})", "<}+", "<},", "<}-", "<}.", "<}/", "<}:", "<};", "<}<", "<}=", "<}>", "<}?", "<}^", "<}_", "<}{", "<}|", "<}}", "<}~", "<~ ", "<~#", "<~$", "<~%", "<~&", "<~(", "<~)", "<~+", "<~,", "<~-", "<~.", "<~/", "<~:", "<~;", "<~<", "<~=", "<~>", "<~?", "<~^", "<~_", "<~{", "<~|", "<~}", "<~~", "=  ", "= #", "= $", "= &", "= (", "= )", "= ;", "= <", "= >", "= ?", "= |", "=#$", "=#&", "=#(", "=#)", "=#;", "=#<", "=#>", "=#|", "=$#", "=$$", "=$&", "=$(", "=$)", "=$-", "=$;", "=$<", "=$>", "=$?", "=$_", "=${", "=$|", "=%$", "=%&", "=%(", "=%)", "=%;", "=%<", "=%>", "=%|", "=& ", "=&#", "=&$", "=&%", "=&&", "=&(", "=&)", "=&+", "=&,", "=&-", "=&.", "=&/", "=&:", "=&;", "=&<", "=&=", "=&>", "=&?", "=&^", "=&_", "=&{", "=&|", "=&}", "=&~", "=( ", "=(#", "=($", "=(%", "=(&", "=((", "=()", "=(+", "=(,", "=(-", "=(.", "=(/", "=(:", "=(;", "=(<", "=(=", "=(>", "=(?", "=(^", "=(_", "=({", "=(|", "=(}", "=(~", "=) ", "=)#", "=)$", "=)%", "=)&", "=)(", "=))", "=)+", "=),", "=)-", "=).", "=)/", "=):", "=);", "=)<", "=)=", "=)>", "=)?", "=)^", "=)_", "=){", "=)|", "=)}", "=)~", "=+$", "=+&", "=+(", "=+)", "=+;", "=+<", "=+>", "=+|", "=,$", "=,&", "=,(", "=,)", "=,;", "=,<", "=,>", "=,|", "=-$", "=-&", "=-(", "=-)", "=-;", "=-<", "=->", "=-|", "=.$", "=.&", "=.(", "=.)", "=.;", "=.<", "=.>", "=.|", "=/$", "=/&", "=/(", "=/)", "=/;", "=/<", "=/>", "=/|", "=:$", "=:&", "=:(", "=:)", "=:;", "=:<", "=:>", "=:|", "=:~", "=; ", "=;#", "=;$", "=;%", "=;&", "=;(", "=;)", "=;+", "=;,", "=;-", "=;.", "=;/", "=;:", "=;;", "=;<", "=;=", "=;>", "=;?", "=;^", "=;_", "=;{", "=;|", "=;}", "=;~", "=< ", "=<#", "=<$", "=<%", "=<&", "=<(", "=<)", "=<+", "=<,", "=<-", "=<.", "=</", "=<:", "=<;", "=<<", "=<=", "=<>", "=<?", "=<^", "=<_", "=<{", "=<|", "=<}", "=<~", "==$", "==&", "==(", "==)", "==;", "==<", "==>", "==|", "=> ", "=>#", "=>$", "=>%", "=>&", "=>(", "=>)", "=>+", "=>,", "=>-", "=>.", "=>/", "=>:", "=>;", "=><", "=>=", "=>>", "=>?", "=>^", "=>_", "=>{", "=>|", "=>}", "=>~", "=?$", "=?&", "=?(", "=?)", "=?;", "=?<", "=?>", "=?|", "=^$", "=^&", "=^(", "=^)", "=^;", "=^<", "=^>", "=^|", "=_$", "=_&", "=_(", "=_)", "=_;", "=_<", "=_>", "=_|", "={$", "={&", "={(", "={)", "={;", "={<", "={>", "={|", "=| ", "=|#", "=|$", "=|%", "=|&", "=|(", "=|)", "=|+", "=|,", "=|-", "=|.", "=|/", "=|:", "=|;", "=|<", "=|=", "=|>", "=|?", "=|^", "=|_", "=|{", "=||", "=|}", "=|~", "=} ", "=}$", "=}&", "=}(", "=})", "=};", "=}<", "=}>", "=}|", "=~$", "=~&", "=~(", "=~)", "=~;", "=~<", "=~>", "=~|", ">  ", "> #", "> $", "> %", "> &", "> (", "> )", "> +", "> ,", "> -", "> .", "> /", "> :", "> ;", "> <", "> =", "> >", "> ?", "> ^", "> _", "> {", "> |", "> }", "> ~", "># ", ">##", ">#$", ">#%", ">#&", ">#(", ">#)", ">#+", ">#,", ">#-", ">#.", ">#/", ">#:", ">#;", ">#<", ">#=", ">#>", ">#?", ">#^", ">#_", ">#{", ">#|", ">#}", ">#~", ">$ ", ">$#", ">$$", ">$%", ">$&", ">$(", ">$)", ">$+", ">$,", ">$-", ">$.", ">$/", ">$:", ">$;", ">$<", ">$=", ">$>", ">$?", ">$^", ">$_", ">${", ">$|", ">$}", ">$~", ">% ", ">%#", ">%$", ">%%", ">%&", ">%(", ">%)", ">%+", ">%,", ">%-", ">%.", ">%/", ">%:", ">%;", ">%<", ">%=", ">%>", ">%?", ">%^", ">%_", ">%{", ">%|", ">%}", ">%~", ">& ", ">&#", ">&$", ">&%", ">&&", ">&(", ">&)", ">&+", ">&,", ">&-", ">&.", ">&/", ">&:", ">&;", ">&<", ">&=", ">&>", ">&?", ">&^", ">&_", ">&{", ">&|", ">&}", ">&~", ">( ", ">(#", ">($", ">(%", ">(&", ">((", ">()", ">(+", ">(,", ">(-", ">(.", ">(/", ">(:", ">(;", ">(<", ">(=", ">(>", ">(?", ">(^", ">(_", ">({", ">(|", ">(}", ">(~", ">) ", ">)#", ">)$", ">)%", ">)&", ">)(", ">))", ">)+", ">),", ">)-", ">).", ">)/", ">):", ">);", ">)<", ">)=", ">)>", ">)?", ">)^", ">)_", ">){", ">)|", ">)}", ">)~", ">+ ", ">+#", ">+$", ">+%", ">+&", ">+(", ">+)", ">++", ">+,", ">+-", ">+.", ">+/", ">+:", ">+;", ">+<", ">+=", ">+>", ">+?", ">+^", ">+_", ">+{", ">+|", ">+}", ">+~", ">, ", ">,#", ">,$", ">,%", ">,&", ">,(", ">,)", ">,+", ">,,", ">,-", ">,.", ">,/", ">,:", ">,;", ">,<", ">,=", ">,>", ">,?", ">,^", ">,_", ">,{", ">,|", ">,}", ">,~", ">- ", ">-#", ">-$", ">-%", ">-&", ">-(", ">-)", ">-+", ">-,", ">--", ">-.", ">-/", ">-:", ">-;", ">-<", ">-=", ">->", ">-?", ">-^", ">-_", ">-{", ">-|", ">-}", ">-~", ">. ", ">.#", ">.$", ">.%", ">.&", ">.(", ">.)", ">.+", ">.,", ">.-", ">..", ">./", ">.:", ">.;", ">.<", ">.=", ">.>", ">.?", ">.^", ">._", ">.{", ">.|", ">.}", ">.~", ">/ ", ">/#", ">/$", ">/%", ">/&", ">/(", ">/)", ">/+", ">/,", ">/-", ">/.", ">//", ">/:", ">/;", ">/<", ">/=", ">/>", ">/?", ">/^", ">/_", ">/{", ">/|", ">/}", ">/~", ">: ", ">:#", ">:$", ">:%", ">:&", ">:(", ">:)", ">:+", ">:,", ">:-", ">:.", ">:/", ">::", ">:;", ">:<", ">:=", ">:>", ">:?", ">:^", ">:_", ">:{", ">:|", ">:}", ">:~", ">; ", ">;#", ">;$", ">;%", ">;&", ">;(", ">;)", ">;+", ">;,", ">;-", ">;.", ">;/", ">;:", ">;;", ">;<", ">;=", ">;>", ">;?", ">;^", ">;_", ">;{", ">;|", ">;}", ">;~", ">< ", "><#", "><$", "><%", "><&", "><(", "><)", "><+", "><,", "><-", "><.", "></", "><:", "><;", "><<", "><=", "><>", "><?", "><^", "><_", "><{", "><|", "><}", "><~", ">= ", ">=#", ">=$", ">=%", ">=&", ">=(", ">=)", ">=+", ">=,", ">=-", ">=.", ">=/", ">=:", ">=;", ">=<", ">==", ">=>", ">=?", ">=^", ">=_", ">={", ">=|", ">=}", ">=~", ">> ", ">>#", ">>$", ">>%", ">>&", ">>(", ">>)", ">>+", ">>,", ">>-", ">>.", ">>/", ">>:", ">>;", ">><", ">>=", ">>>", ">>?", ">>^", ">>_", ">>{", ">>|", ">>}", ">>~", ">? ", ">?#", ">?$", ">?%", ">?&", ">?(", ">?)", ">?+", ">?,", ">?-", ">?.", ">?/", ">?:", ">?;", ">?<", ">?=", ">?>", ">??", ">?^", ">?_", ">?{", ">?|", ">?}", ">?~", ">^ ", ">^#", ">^$", ">^%", ">^&", ">^(", ">^)", ">^+", ">^,", ">^-", ">^.", ">^/", ">^:", ">^;", ">^<", ">^=", ">^>", ">^?", ">^^", ">^_", ">^{", ">^|", ">^}", ">^~", ">_ ", ">_#", ">_$", ">_%", ">_&", ">_(", ">_)", ">_+", ">_,", ">_-", ">_.", ">_/", ">_:", ">_;", ">_<", ">_=", ">_>", ">_?", ">_^", ">__", ">_{", ">_|", ">_}", ">_~", ">{ ", ">{#", ">{$", ">{%", ">{&", ">{(", ">{)", ">{+", ">{,", ">{-", ">{.", ">{/", ">{:", ">{;", ">{<", ">{=", ">{>", ">{?", ">{^", ">{_", ">{{", ">{|", ">{}", ">{~", ">| ", ">|#", ">|$", ">|%", ">|&", ">|(", ">|)", ">|+", ">|,", ">|-", ">|.", ">|/", ">|:", ">|;", ">|<", ">|=", ">|>", ">|?", ">|^", ">|_", ">|{", ">||", ">|}", ">|~", ">} ", ">}#", ">}$", ">}%", ">}&", ">}(", ">})", ">}+", ">},", ">}-", ">}.", ">}/", ">}:", ">};", ">}<", ">}=", ">}>", ">}?", ">}^", ">}_", ">}{", ">}|", ">}}", ">}~", ">~ ", ">~#", ">~$", ">~%", ">~&", ">~(", ">~)", ">~+", ">~,", ">~-", ">~.", ">~/", ">~:", ">~;", ">~<", ">~=", ">~>", ">~?", ">~^", ">~_", ">~{", ">~|", ">~}", ">~~", "?  ", "? #", "? $", "? &", "? (", "? )", "? ;", "? <", "? >", "? ?", "? |", "?#$", "?#&", "?#(", "?#)", "?#;", "?#<", "?#>", "?#|", "?$#", "?$$", "?$&", "?$(", "?$)", "?$-", "?$;", "?$<", "?$>", "?$?", "?$_", "?${", "?$|", "?%$", "?%&", "?%(", "?%)", "?%;", "?%<", "?%>", "?%|", "?& ", "?&#", "?&$", "?&%", "?&&", "?&(", "?&)", "?&+", "?&,", "?&-", "?&.", "?&/", "?&:", "?&;", "?&<", "?&=", "?&>", "?&?", "?&^", "?&_", "?&{", "?&|", "?&}", "?&~", "?( ", "?(#", "?($", "?(%", "?(&", "?((", "?()", "?(+", "?(,", "?(-", "?(.", "?(/", "?(:", "?(;", "?(<", "?(=", "?(>", "?(?", "?(^", "?(_", "?({", "?(|", "?(}", "?(~", "?) ", "?)#", "?)$", "?)%", "?)&", "?)(", "?))", "?)+", "?),", "?)-", "?).", "?)/", "?):", "?);", "?)<", "?)=", "?)>", "?)?", "?)^", "?)_", "?){", "?)|", "?)}", "?)~", "?+$", "?+&", "?+(", "?+)", "?+;", "?+<", "?+>", "?+|", "?,$", "?,&", "?,(", "?,)", "?,;", "?,<", "?,>", "?,|", "?-$", "?-&", "?-(", "?-)", "?-;", "?-<", "?->", "?-|", "?.$", "?.&", "?.(", "?.)", "?.;", "?.<", "?.>", "?.|", "?/$", "?/&", "?/(", "?/)", "?/;", "?/<", "?/>", "?/|", "?:$", "?:&", "?:(", "?:)", "?:;", "?:<", "?:>", "?:|", "?:~", "?; ", "?;#", "?;$", "?;%", "?;&", "?;(", "?;)", "?;+", "?;,", "?;-", "?;.", "?;/", "?;:", "?;;", "?;<", "?;=", "?;>", "?;?", "?;^", "?;_", "?;{", "?;|", "?;}", "?;~", "?< ", "?<#", "?<$", "?<%", "?<&", "?<(", "?<)", "?<+", "?<,", "?<-", "?<.", "?</", "?<:", "?<;", "?<<", "?<=", "?<>", "?<?", "?<^", "?<_", "?<{", "?<|", "?<}", "?<~", "?=$", "?=&", "?=(", "?=)", "?=;", "?=<", "?=>", "?=|", "?> ", "?>#", "?>$", "?>%", "?>&", "?>(", "?>)", "?>+", "?>,", "?>-", "?>.", "?>/", "?>:", "?>;", "?><", "?>=", "?>>", "?>?", "?>^", "?>_", "?>{", "?>|", "?>}", "?>~", "??$", "??&", "??(", "??)", "??;", "??<", "??>", "??|", "?^$", "?^&", "?^(", "?^)", "?^;", "?^<", "?^>", "?^|", "?_$", "?_&", "?_(", "?_)", "?_;", "?_<", "?_>", "?_|", "?{$", "?{&", "?{(", "?{)", "?{;", "?{<", "?{>", "?{|", "?| ", "?|#", "?|$", "?|%", "?|&", "?|(", "?|)", "?|+", "?|,", "?|-", "?|.", "?|/", "?|:", "?|;", "?|<", "?|=", "?|>", "?|?", "?|^", "?|_", "?|{", "?||", "?|}", "?|~", "?} ", "?}$", "?}&", "?}(", "?})", "?};", "?}<", "?}>", "?}|", "?~$", "?~&", "?~(", "?~)", "?~;", "?~<", "?~>", "?~|", "^  ", "^ #", "^ $", "^ &", "^ (", "^ )", "^ ;", "^ <", "^ >", "^ ?", "^ |", "^#$", "^#&", "^#(", "^#)", "^#;", "^#<", "^#>", "^#|", "^$#", "^$$", "^$&", "^$(", "^$)", "^$-", "^$;", "^$<", "^$>", "^$?", "^$_", "^${", "^$|", "^%$", "^%&", "^%(", "^%)", "^%;", "^%<", "^%>", "^%|", "^& ", "^&#", "^&$", "^&%", "^&&", "^&(", "^&)", "^&+", "^&,", "^&-", "^&.", "^&/", "^&:", "^&;", "^&<", "^&=", "^&>", "^&?", "^&^", "^&_", "^&{", "^&|", "^&}", "^&~", "^( ", "^(#", "^($", "^(%", "^(&", "^((", "^()", "^(+", "^(,", "^(-", "^(.", "^(/", "^(:", "^(;", "^(<", "^(=", "^(>", "^(?", "^(^", "^(_", "^({", "^(|", "^(}", "^(~", "^) ", "^)#", "^)$", "^)%", "^)&", "^)(", "^))", "^)+", "^),", "^)-", "^).", "^)/", "^):", "^);", "^)<", "^)=", "^)>", "^)?", "^)^", "^)_", "^){", "^)|", "^)}", "^)~", "^+$", "^+&", "^+(", "^+)", "^+;", "^+<", "^+>", "^+|", "^,$", "^,&", "^,(", "^,)", "^,;", "^,<", "^,>", "^,|", "^-$", "^-&", "^-(", "^-)", "^-;", "^-<", "^->", "^-|", "^.$", "^.&", "^.(", "^.)", "^.;", "^.<", "^.>", "^.|", "^/$", "^/&", "^/(", "^/)", "^/;", "^/<", "^/>", "^/|", "^:$", "^:&", "^:(", "^:)", "^:;", "^:<", "^:>", "^:|", "^:~", "^; ", "^;#", "^;$", "^;%", "^;&", "^;(", "^;)", "^;+", "^;,", "^;-", "^;.", "^;/", "^;:", "^;;", "^;<", "^;=", "^;>", "^;?", "^;^", "^;_", "^;{", "^;|", "^;}", "^;~", "^< ", "^<#", "^<$", "^<%", "^<&", "^<(", "^<)", "^<+", "^<,", "^<-", "^<.", "^</", "^<:", "^<;", "^<<", "^<=", "^<>", "^<?", "^<^", "^<_", "^<{", "^<|", "^<}", "^<~", "^=$", "^=&", "^=(", "^=)", "^=;", "^=<", "^=>", "^=|", "^> ", "^>#", "^>$", "^>%", "^>&", "^>(", "^>)", "^>+", "^>,", "^>-", "^>.", "^>/", "^>:", "^>;", "^><", "^>=", "^>>", "^>?", "^>^", "^>_", "^>{", "^>|", "^>}", "^>~", "^?$", "^?&", "^?(", "^?)", "^?;", "^?<", "^?>", "^?|", "^^$", "^^&", "^^(", "^^)", "^^;", "^^<", "^^>", "^^|", "^_$", "^_&", "^_(", "^_)", "^_;", "^_<", "^_>", "^_|", "^{$", "^{&", "^{(", "^{)", "^{;", "^{<", "^{>", "^{|", "^| ", "^|#", "^|$", "^|%", "^|&", "^|(", "^|)", "^|+", "^|,", "^|-", "^|.", "^|/", "^|:", "^|;", "^|<", "^|=", "^|>", "^|?", "^|^", "^|_", "^|{", "^||", "^|}", "^|~", "^} ", "^}$", "^}&", "^}(", "^})", "^};", "^}<", "^}>", "^}|", "^~$", "^~&", "^~(", "^~)", "^~;", "^~<", "^~>", "^~|", "_  ", "_ #", "_ $", "_ &", "_ (", "_ )", "_ ;", "_ <", "_ >", "_ ?", "_ |", "_#$", "_#&", "_#(", "_#)", "_#;", "_#<", "_#>", "_#|", "_$#", "_$$", "_$&", "_$(", "_$)", "_$-", "_$;", "_$<", "_$>", "_$?", "_$_", "_${", "_$|", "_%$", "_%&", "_%(", "_%)", "_%;", "_%<", "_%>", "_%|", "_& ", "_&#", "_&$", "_&%", "_&&", "_&(", "_&)", "_&+", "_&,", "_&-", "_&.", "_&/", "_&:", "_&;", "_&<", "_&=", "_&>", "_&?", "_&^", "_&_", "_&{", "_&|", "_&}", "_&~", "_( ", "_(#", "_($", "_(%", "_(&", "_((", "_()", "_(+", "_(,", "_(-", "_(.", "_(/", "_(:", "_(;", "_(<", "_(=", "_(>", "_(?", "_(^", "_(_", "_({", "_(|", "_(}", "_(~", "_) ", "_)#", "_)$", "_)%", "_)&", "_)(", "_))", "_)+", "_),", "_)-", "_).", "_)/", "_):", "_);", "_)<", "_)=", "_)>", "_)?", "_)^", "_)_", "_){", "_)|", "_)}", "_)~", "_+$", "_+&", "_+(", "_+)", "_+;", "_+<", "_+>", "_+|", "_,$", "_,&", "_,(", "_,)", "_,;", "_,<", "_,>", "_,|", "_-$", "_-&", "_-(", "_-)", "_-;", "_-<", "_->", "_-|", "_.$", "_.&", "_.(", "_.)", "_.;", "_.<", "_.>", "_.|", "_/$", "_/&", "_/(", "_/)", "_/;", "_/<", "_/>", "_/|", "_:$", "_:&", "_:(", "_:)", "_:;", "_:<", "_:>", "_:|", "_:~", "_; ", "_;#", "_;$", "_;%", "_;&", "_;(", "_;)", "_;+", "_;,", "_;-", "_;.", "_;/", "_;:", "_;;", "_;<", "_;=", "_;>", "_;?", "_;^", "_;_", "_;{", "_;|", "_;}", "_;~", "_< ", "_<#", "_<$", "_<%", "_<&", "_<(", "_<)", "_<+", "_<,", "_<-", "_<.", "_</", "_<:", "_<;", "_<<", "_<=", "_<>", "_<?", "_<^", "_<_", "_<{", "_<|", "_<}", "_<~", "_=$", "_=&", "_=(", "_=)", "_=;", "_=<", "_=>", "_=|", "_> ", "_>#", "_>$", "_>%", "_>&", "_>(", "_>)", "_>+", "_>,", "_>-", "_>.", "_>/", "_>:", "_>;", "_><", "_>=", "_>>", "_>?", "_>^", "_>_", "_>{", "_>|", "_>}", "_>~", "_?$", "_?&", "_?(", "_?)", "_?;", "_?<", "_?>", "_?|", "_^$", "_^&", "_^(", "_^)", "_^;", "_^<", "_^>", "_^|", "__$", "__&", "__(", "__)", "__;", "__<", "__>", "__|", "_{$", "_{&", "_{(", "_{)", "_{;", "_{<", "_{>", "_{|", "_| ", "_|#", "_|$", "_|%", "_|&", "_|(", "_|)", "_|+", "_|,", "_|-", "_|.", "_|/", "_|:", "_|;", "_|<", "_|=", "_|>", "_|?", "_|^", "_|_", "_|{", "_||", "_|}", "_|~", "_} ", "_}$", "_}&", "_}(", "_})", "_};", "_}<", "_}>", "_}|", "_~$", "_~&", "_~(", "_~)", "_~;", "_~<", "_~>", "_~|", "{  ", "{ #", "{ $", "{ &", "{ (", "{ )", "{ ;", "{ <", "{ >", "{ ?", "{ |", "{#$", "{#&", "{#(", "{#)", "{#;", "{#<", "{#>", "{#|", "{$#", "{$$", "{$&", "{$(", "{$)", "{$-", "{$;", "{$<", "{$>", "{$?", "{$_", "{${", "{$|", "{%$", "{%&", "{%(", "{%)", "{%;", "{%<", "{%>", "{%|", "{& ", "{&#", "{&$", "{&%", "{&&", "{&(", "{&)", "{&+", "{&,", "{&-", "{&.", "{&/", "{&:", "{&;", "{&<", "{&=", "{&>", "{&?", "{&^", "{&_", "{&{", "{&|", "{&}", "{&~", "{( ", "{(#", "{($", "{(%", "{(&", "{((", "{()", "{(+", "{(,", "{(-", "{(.", "{(/", "{(:", "{(;", "{(<", "{(=", "{(>", "{(?", "{(^", "{(_", "{({", "{(|", "{(}", "{(~", "{) ", "{)#", "{)$", "{)%", "{)&", "{)(", "{))", "{)+", "{),", "{)-", "{).", "{)/", "{):", "{);", "{)<", "{)=", "{)>", "{)?", "{)^", "{)_", "{){", "{)|", "{)}", "{)~", "{+$", "{+&", "{+(", "{+)", "{+;", "{+<", "{+>", "{+|", "{,$", "{,&", "{,(", "{,)", "{,;", "{,<", "{,>", "{,|", "{,}", "{-$", "{-&", "{-(", "{-)", "{-;", "{-<", "{->", "{-|", "{.$", "{.&", "{.(", "{.)", "{.;", "{.<", "{.>", "{.|", "{/$", "{/&", "{/(", "{/)", "{/;", "{/<", "{/>", "{/|", "{:$", "{:&", "{:(", "{:)", "{:;", "{:<", "{:>", "{:|", "{:~", "{; ", "{;#", "{;$", "{;%", "{;&", "{;(", "{;)", "{;+", "{;,", "{;-", "{;.", "{;/", "{;:", "{;;", "{;<", "{;=", "{;>", "{;?", "{;^", "{;_", "{;{", "{;|", "{;}", "{;~", "{< ", "{<#", "{<$", "{<%", "{<&", "{<(", "{<)", "{<+", "{<,", "{<-", "{<.", "{</", "{<:", "{<;", "{<<", "{<=", "{<>", "{<?", "{<^", "{<_", "{<{", "{<|", "{<}", "{<~", "{=$", "{=&", "{=(", "{=)", "{=;", "{=<", "{=>", "{=|", "{> ", "{>#", "{>$", "{>%", "{>&", "{>(", "{>)", "{>+", "{>,", "{>-", "{>.", "{>/", "{>:", "{>;", "{><", "{>=", "{>>", "{>?", "{>^", "{>_", "{>{", "{>|", "{>}", "{>~", "{?$", "{?&", "{?(", "{?)", "{?;", "{?<", "{?>", "{?|", "{^$", "{^&", "{^(", "{^)", "{^;", "{^<", "{^>", "{^|", "{_$", "{_&", "{_(", "{_)", "{_;", "{_<", "{_>", "{_|", "{{$", "{{&", "{{(", "{{)", "{{;", "{{<", "{{>", "{{|", "{| ", "{|#", "{|$", "{|%", "{|&", "{|(", "{|)", "{|+", "{|,", "{|-", "{|.", "{|/", "{|:", "{|;", "{|<", "{|=", "{|>", "{|?", "{|^", "{|_", "{|{", "{||", "{|}", "{|~", "{} ", "{}$", "{}&", "{}(", "{})", "{};", "{}<", "{}>", "{}|", "{~$", "{~&", "{~(", "{~)", "{~;", "{~<", "{~>", "{~|", "|  ", "| #", "| $", "| %", "| &", "| (", "| )", "| +", "| ,", "| -", "| .", "| /", "| :", "| ;", "| <", "| =", "| >", "| ?", "| ^", "| _", "| {", "| |", "| }", "| ~", "|# ", "|##", "|#$", "|#%", "|#&", "|#(", "|#)", "|#+", "|#,", "|#-", "|#.", "|#/", "|#:", "|#;", "|#<", "|#=", "|#>", "|#?", "|#^", "|#_", "|#{", "|#|", "|#}", "|#~", "|$ ", "|$#", "|$$", "|$%", "|$&", "|$(", "|$)", "|$+", "|$,", "|$-", "|$.", "|$/", "|$:", "|$;", "|$<", "|$=", "|$>", "|$?", "|$^", "|$_", "|${", "|$|", "|$}", "|$~", "|% ", "|%#", "|%$", "|%%", "|%&", "|%(", "|%)", "|%+", "|%,", "|%-", "|%.", "|%/", "|%:", "|%;", "|%<", "|%=", "|%>", "|%?", "|%^", "|%_", "|%{", "|%|", "|%}", "|%~", "|& ", "|&#", "|&$", "|&%", "|&&", "|&(", "|&)", "|&+", "|&,", "|&-", "|&.", "|&/", "|&:", "|&;", "|&<", "|&=", "|&>", "|&?", "|&^", "|&_", "|&{", "|&|", "|&}", "|&~", "|( ", "|(#", "|($", "|(%", "|(&", "|((", "|()", "|(+", "|(,", "|(-", "|(.", "|(/", "|(:", "|(;", "|(<", "|(=", "|(>", "|(?", "|(^", "|(_", "|({", "|(|", "|(}", "|(~", "|) ", "|)#", "|)$", "|)%", "|)&", "|)(", "|))", "|)+", "|),", "|)-", "|).", "|)/", "|):", "|);", "|)<", "|)=", "|)>", "|)?", "|)^", "|)_", "|){", "|)|", "|)}", "|)~", "|+ ", "|+#", "|+$", "|+%", "|+&", "|+(", "|+)", "|++", "|+,", "|+-", "|+.", "|+/", "|+:", "|+;", "|+<", "|+=", "|+>", "|+?", "|+^", "|+_", "|+{", "|+|", "|+}", "|+~", "|, ", "|,#", "|,$", "|,%", "|,&", "|,(", "|,)", "|,+", "|,,", "|,-", "|,.", "|,/", "|,:", "|,;", "|,<", "|,=", "|,>", "|,?", "|,^", "|,_", "|,{", "|,|", "|,}", "|,~", "|- ", "|-#", "|-$", "|-%", "|-&", "|-(", "|-)", "|-+", "|-,", "|--", "|-.", "|-/", "|-:", "|-;", "|-<", "|-=", "|->", "|-?", "|-^", "|-_", "|-{", "|-|", "|-}", "|-~", "|. ", "|.#", "|.$", "|.%", "|.&", "|.(", "|.)", "|.+", "|.,", "|.-", "|..", "|./", "|.:", "|.;", "|.<", "|.=", "|.>", "|.?", "|.^", "|._", "|.{", "|.|", "|.}", "|.~", "|/ ", "|/#", "|/$", "|/%", "|/&", "|/(", "|/)", "|/+", "|/,", "|/-", "|/.", "|//", "|/:", "|/;", "|/<", "|/=", "|/>", "|/?", "|/^", "|/_", "|/{", "|/|", "|/}", "|/~", "|: ", "|:#", "|:$", "|:%", "|:&", "|:(", "|:)", "|:+", "|:,", "|:-", "|:.", "|:/", "|::", "|:;", "|:<", "|:=", "|:>", "|:?", "|:^", "|:_", "|:{", "|:|", "|:}", "|:~", "|; ", "|;#", "|;$", "|;%", "|;&", "|;(", "|;)", "|;+", "|;,", "|;-", "|;.", "|;/", "|;:", "|;;", "|;<", "|;=", "|;>", "|;?", "|;^", "|;_", "|;{", "|;|", "|;}", "|;~", "|< ", "|<#", "|<$", "|<%", "|<&", "|<(", "|<)", "|<+", "|<,", "|<-", "|<.", "|</", "|<:", "|<;", "|<<", "|<=", "|<>", "|<?", "|<^", "|<_", "|<{", "|<|", "|<}", "|<~", "|= ", "|=#", "|=$", "|=%", "|=&", "|=(", "|=)", "|=+", "|=,", "|=-", "|=.", "|=/", "|=:", "|=;", "|=<", "|==", "|=>", "|=?", "|=^", "|=_", "|={", "|=|", "|=}", "|=~", "|> ", "|>#", "|>$", "|>%", "|>&", "|>(", "|>)", "|>+", "|>,", "|>-", "|>.", "|>/", "|>:", "|>;", "|><", "|>=", "|>>", "|>?", "|>^", "|>_", "|>{", "|>|", "|>}", "|>~", "|? ", "|?#", "|?$", "|?%", "|?&", "|?(", "|?)", "|?+", "|?,", "|?-", "|?.", "|?/", "|?:", "|?;", "|?<", "|?=", "|?>", "|??", "|?^", "|?_", "|?{", "|?|", "|?}", "|?~", "|^ ", "|^#", "|^$", "|^%", "|^&", "|^(", "|^)", "|^+", "|^,", "|^-", "|^.", "|^/", "|^:", "|^;", "|^<", "|^=", "|^>", "|^?", "|^^", "|^_", "|^{", "|^|", "|^}", "|^~", "|_ ", "|_#", "|_$", "|_%", "|_&", "|_(", "|_)", "|_+", "|_,", "|_-", "|_.", "|_/", "|_:", "|_;", "|_<", "|_=", "|_>", "|_?", "|_^", "|__", "|_{", "|_|", "|_}", "|_~", "|{ ", "|{#", "|{$", "|{%", "|{&", "|{(", "|{)", "|{+", "|{,", "|{-", "|{.", "|{/", "|{:", "|{;", "|{<", "|{=", "|{>", "|{?", "|{^", "|{_", "|{{", "|{|", "|{}", "|{~", "|| ", "||#", "||$", "||%", "||&", "||(", "||)", "||+", "||,", "||-", "||.", "||/", "||:", "||;", "||<", "||=", "||>", "||?", "||^", "||_", "||{", "|||", "||}", "||~", "|} ", "|}#", "|}$", "|}%", "|}&", "|}(", "|})", "|}+", "|},", "|}-", "|}.", "|}/", "|}:", "|};", "|}<", "|}=", "|}>", "|}?", "|}^", "|}_", "|}{", "|}|", "|}}", "|}~", "|~ ", "|~#", "|~$", "|~%", "|~&", "|~(", "|~)", "|~+", "|~,", "|~-", "|~.", "|~/", "|~:", "|~;", "|~<", "|~=", "|~>", "|~?", "|~^", "|~_", "|~{", "|~|", "|~}", "|~~", "}  ", "} #", "} $", "} %", "} &", "} (", "} )", "} +", "} ,", "} -", "} .", "} /", "} :", "} ;", "} <", "} =", "} >", "} ?", "} ^", "} _", "} {", "} |", "} }", "} ~", "}# ", "}#$", "}#&", "}#(", "}#)", "}#;", "}#<", "}#>", "}#|", "}$ ", "}$#", "}$$", "}$&", "}$(", "}$)", "}$-", "}$;", "}$<", "}$>", "}$?", "}$_", "}${", "}$|", "}% ", "}%$", "}%&", "}%(", "}%)", "}%;", "}%<", "}%>", "}%|", "}& ", "}&#", "}&$", "}&%", "}&&", "}&(", "}&)", "}&+", "}&,", "}&-", "}&.", "}&/", "}&:", "}&;", "}&<", "}&=", "}&>", "}&?", "}&^", "}&_", "}&{", "}&|", "}&}", "}&~", "}( ", "}(#", "}($", "}(%", "}(&", "}((", "}()", "}(+", "}(,", "}(-", "}(.", "}(/", "}(:", "}(;", "}(<", "}(=", "}(>", "}(?", "}(^", "}(_", "}({", "}(|", "}(}", "}(~", "}) ", "})#", "})$", "})%", "})&", "})(", "}))", "})+", "}),", "})-", "}).", "})/", "}):", "});", "})<", "})=", "})>", "})?", "})^", "})_", "}){", "})|", "})}", "})~", "}+ ", "}+$", "}+&", "}+(", "}+)", "}+;", "}+<", "}+>", "}+|", "}, ", "},$", "},&", "},(", "},)", "},;", "},<", "},>", "},|", "}- ", "}-$", "}-&", "}-(", "}-)", "}-;", "}-<", "}->", "}-|", "}. ", "}.$", "}.&", "}.(", "}.)", "}.;", "}.<", "}.>", "}.|", "}/ ", "}/$", "}/&", "}/(", "}/)", "}/;", "}/<", "}/>", "}/|", "}: ", "}:$", "}:&", "}:(", "}:)", "}:;", "}:<", "}:>", "}:|", "}:~", "}; ", "};#", "};$", "};%", "};&", "};(", "};)", "};+", "};,", "};-", "};.", "};/", "};:", "};;", "};<", "};=", "};>", "};?", "};^", "};_", "};{", "};|", "};}", "};~", "}< ", "}<#", "}<$", "}<%", "}<&", "}<(", "}<)", "}<+", "}<,", "}<-", "}<.", "}</", "}<:", "}<;", "}<<", "}<=", "}<>", "}<?", "}<^", "}<_", "}<{", "}<|", "}<}", "}<~", "}= ", "}=$", "}=&", "}=(", "}=)", "}=;", "}=<", "}=>", "}=|", "}> ", "}>#", "}>$", "}>%", "}>&", "}>(", "}>)", "}>+", "}>,", "}>-", "}>.", "}>/", "}>:", "}>;", "}><", "}>=", "}>>", "}>?", "}>^", "}>_", "}>{", "}>|", "}>}", "}>~", "}? ", "}?$", "}?&", "}?(", "}?)", "}?;", "}?<", "}?>", "}?|", "}^ ", "}^$", "}^&", "}^(", "}^)", "}^;", "}^<", "}^>", "}^|", "}_ ", "}_$", "}_&", "}_(", "}_)", "}_;", "}_<", "}_>", "}_|", "}{ ", "}{$", "}{&", "}{(", "}{)", "}{,", "}{;", "}{<", "}{>", "}{|", "}| ", "}|#", "}|$", "}|%", "}|&", "}|(", "}|)", "}|+", "}|,", "}|-", "}|.", "}|/", "}|:", "}|;", "}|<", "}|=", "}|>", "}|?", "}|^", "}|_", "}|{", "}||", "}|}", "}|~", "}} ", "}}$", "}}&", "}}(", "}})", "}};", "}}<", "}}>", "}}|", "}~ ", "}~$", "}~&", "}~(", "}~)", "}~;", "}~<", "}~>", "}~|", "~  ", "~ #", "~ $", "~ &", "~ (", "~ )", "~ ;", "~ <", "~ >", "~ ?", "~ |", "~#$", "~#&", "~#(", "~#)", "~#;", "~#<", "~#>", "~#|", "~$#", "~$$", "~$&", "~$(", "~$)", "~$-", "~$;", "~$<", "~$>", "~$?", "~$_", "~${", "~$|", "~%$", "~%&", "~%(", "~%)", "~%;", "~%<", "~%>", "~%|", "~& ", "~&#", "~&$", "~&%", "~&&", "~&(", "~&)", "~&+", "~&,", "~&-", "~&.", "~&/", "~&:", "~&;", "~&<", "~&=", "~&>", "~&?", "~&^", "~&_", "~&{", "~&|", "~&}", "~&~", "~( ", "~(#", "~($", "~(%", "~(&", "~((", "~()", "~(+", "~(,", "~(-", "~(.", "~(/", "~(:", "~(;", "~(<", "~(=", "~(>", "~(?", "~(^", "~(_", "~({", "~(|", "~(}", "~(~", "~) ", "~)#", "~)$", "~)%", "~)&", "~)(", "~))", "~)+", "~),", "~)-", "~).", "~)/", "~):", "~);", "~)<", "~)=", "~)>", "~)?", "~)^", "~)_", "~){", "~)|", "~)}", "~)~", "~+$", "~+&", "~+(", "~+)", "~+/", "~+:", "~+;", "~+<", "~+>", "~+|", "~,$", "~,&", "~,(", "~,)", "~,;", "~,<", "~,>", "~,|", "~-$", "~-&", "~-(", "~-)", "~-/", "~-:", "~-;", "~-<", "~->", "~-|", "~.$", "~.&", "~.(", "~.)", "~.;", "~.<", "~.>", "~.|", "~/ ", "~/#", "~/$", "~/%", "~/&", "~/(", "~/)", "~/+", "~/,", "~/-", "~/.", "~//", "~/:", "~/;", "~/<", "~/=", "~/>", "~/?", "~/^", "~/_", "~/{", "~/|", "~/}", "~/~", "~: ", "~:#", "~:$", "~:%", "~:&", "~:(", "~:)", "~:+", "~:,", "~:-", "~:.", "~:/", "~::", "~:;", "~:<", "~:=", "~:>", "~:?", "~:^", "~:_", "~:{", "~:|", "~:}", "~:~", "~; ", "~;#", "~;$", "~;%", "~;&", "~;(", "~;)", "~;+", "~;,", "~;-", "~;.", "~;/", "~;:", "~;;", "~;<", "~;=", "~;>", "~;?", "~;^", "~;_", "~;{", "~;|", "~;}", "~;~", "~< ", "~<#", "~<$", "~<%", "~<&", "~<(", "~<)", "~<+", "~<,", "~<-", "~<.", "~</", "~<:", "~<;", "~<<", "~<=", "~<>", "~<?", "~<^", "~<_", "~<{", "~<|", "~<}", "~<~", "~=$", "~=&", "~=(", "~=)", "~=;", "~=<", "~=>", "~=|", "~> ", "~>#", "~>$", "~>%", "~>&", "~>(", "~>)", "~>+", "~>,", "~>-", "~>.", "~>/", "~>:", "~>;", "~><", "~>=", "~>>", "~>?", "~>^", "~>_", "~>{", "~>|", "~>}", "~>~", "~?$", "~?&", "~?(", "~?)", "~?;", "~?<", "~?>", "~?|", "~^$", "~^&", "~^(", "~^)", "~^;", "~^<", "~^>", "~^|", "~_$", "~_&", "~_(", "~_)", "~_;", "~_<", "~_>", "~_|", "~{$", "~{&", "~{(", "~{)", "~{;", "~{<", "~{>", "~{|", "~| ", "~|#", "~|$", "~|%", "~|&", "~|(", "~|)", "~|+", "~|,", "~|-", "~|.", "~|/", "~|:", "~|;", "~|<", "~|=", "~|>", "~|?", "~|^", "~|_", "~|{", "~||", "~|}", "~|~", "~} ", "~}$", "~}&", "~}(", "~})", "~};", "~}<", "~}>", "~}|", "~~$", "~~&", "~~(", "~~)", "~~;", "~~<", "~~>", "~~|"]

        while not goodVar:
            symbolVar = self.randGen.randUniqueStr(1, 3, self.symbols)

            if not bashBracesVar:
                if symbolVar not in badVars:
                    goodVar = True

            else:
                if symbolVar not in badBashVars:
                    goodVar = True

        return symbolVar
