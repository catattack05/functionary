import * as functions from './functions.js'

const validParams = ["--function", "--parameters"]
const args = process.argv.slice(2, )

if (args.length != 4 || !validParams.includes(args[0]) || !validParams.includes(args[2])) {
  console.log(
    "Invalid commandline, --function <function_name> --parameters <parameters in JSON format>"
  )
  console.log(`Got: ${args}`)
  process.exit(1)
}

const toCall = args[0] === "--function" ? args[1] : args[3]
const parameters = args[2] === "--parameters" ? args[3] : args[1]

const retVal = functions[toCall].apply(null, [JSON.parse(parameters)])

console.log("==== Output From Command ====")
console.log(JSON.stringify(retVal))
