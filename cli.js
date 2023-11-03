const optionator = require("optionator");
const lint = require("./lint");

module.exports = {
    async execute(args) {
        if (Array.isArray(args)) {
            console.log("CLI args: " + args.slice(2));
        }

        let opt;
        let options;

        try {
            opt = optionator({
                prepend: "node tool [options] [file/dir...]",
                defaults: {
                    concatRepeatedArrays: true,
                    mergeRepeatedObjects: true
                },
                options: [
                    {
                        heading: "Options"
                    },
                    {
                        option: "output-file",
                        alias: "o",
                        type: "path::String",
                        default: "result.json",
                        description: "Specify file to write report to"
                    },
                    {
                        option: "help",
                        alias: "h",
                        type: "Boolean",
                        description: "Show help"
                    }
                ]
            })
            options = opt.parse(args);
        } catch (error) {
            console.log(error.message);
            return 2;
        }

        if (options.help) {
            console.log(opt.generateHelp());
            return 0;
        }

        let files = options._;
        if (files.length === 0) {
            console.error("Error: No files or project specified.");
            console.log(opt.generateHelp());
            return 1;
        }

        await lint.execute(files, options.outputFile);
        return 0;
    }
};
